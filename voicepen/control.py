# coding=utf-8

from time import sleep
import math
import numpy
import json

try:
    import pigpio
except ModuleNotFoundError:
    print("pigpio needed to run")

class VoicePen:
    def __init__(
        self,
        inner_arm=8,                # Arm size (cm)
        outer_arm=8,                # Forearm size (cm)
        servo_1_centre=1700,        # Central shoulder motor pulse-width
        servo_2_centre=1500,        # Central elbow motor pulse-width
        servo_1_degree_ms=-10,      # PW value that equals 1 degree for shoulder motor
        servo_2_degree_ms=10,       # PW value that equals 1 degree for elbow motor
        arm_1_centre=-45,           # Central arm angle
        arm_2_centre=90,            # Central forearm angle
        hysteresis_correction_1=0,  # Histeresys correction for arm (pw)
        hysteresis_correction_2=0,  # Histeresys correction for forearm (pw)
        bounds=[-8, 6, 0, 12],      # Defining maximum plotting area = xi = -8, xf = 0, yi = 6, yf = 12
        wait=None,                  # Wait factor to improve precision
        pw_up=1500,                 # On angle for on/off motor
        pw_down=1100,               # Off angle for on/off motor
    ):

        # Saving default parameters
        self.INNER_ARM = inner_arm
        self.OUTER_ARM = outer_arm

        self.bounds = bounds

        self.servo_1_centre = servo_1_centre
        self.servo_1_degree_ms = servo_1_degree_ms
        self.arm_1_centre = arm_1_centre
        self.hysteresis_correction_1 = hysteresis_correction_1

        self.servo_2_centre = servo_2_centre
        self.servo_2_degree_ms = servo_2_degree_ms
        self.arm_2_centre = arm_2_centre
        self.hysteresis_correction_2 = hysteresis_correction_2

        # Create the pen object, and make sure the pen is up
        self.pen = Pen(vp=self, pw_up=pw_up, pw_down=pw_down)

        # Create Raspberry Pi
        self.rpi = pigpio.pi()

        # PWMs frequency = 50 Hz
        self.rpi.set_PWM_frequency(14, 50)
        self.rpi.set_PWM_frequency(15, 50)

        # Take motors to the centre
        self.rpi.set_servo_pulsewidth(14, self.angles_to_pw_1(-90))
        sleep(0.3)
        self.rpi.set_servo_pulsewidth(15, self.angles_to_pw_2(90))
        sleep(0.3)

        # Fator de tempo de espera entre movimentos para melhorar precisão, 0.1 como default
        self.wait = wait or .1

        # Setando a posição atual da caneta (já que mandamos os motores para o centro)
        self.current_x = -self.INNER_ARM
        self.current_y = self.OUTER_ARM

        # Ainda to em duvida nisso aqui
        self.angle_1 = self.angle_2 = None

        self.previous_pw_1 = self.previous_pw_2 = 0
        self.active_hysteresis_correction_1 = self.active_hysteresis_correction_2 = 0


    # Aqui, se deixar os dois parametros em true, tanto o flip na linha 204 quanto o flip da linha 215, ele escreve "fora" da caixa mas escreve como nós lemos do jeito normal, mas eu ainda prreciso conferir; interpolate entre 100 e 200 da os melhores resultados
    def plot_file(self, filename="", wait=0, interpolate=100, bounds=None):

        wait = wait or self.wait
        bounds = bounds or self.bounds

        if not bounds:
            return "File plotting is only possible when BrachioGraph.bounds is set."

        with open(filename, "r") as line_file:
            lines = json.load(line_file)

        self.plot_lines(lines=lines, wait=wait, interpolate=interpolate, bounds=bounds, flip=True)


    def plot_lines(self, lines=[], wait=0, interpolate=100, rotate=False, flip=False, bounds=None):

        wait = wait or self.wait
        bounds = bounds or self.bounds

        if not bounds:
            return "Line plotting is only possible when BrachioGraph.bounds is set."

        # Começa o processo de escrita, linha por linha
        for line in lines:
            x, y = line[0]

            #  Se não estamos dentro de 1mm para início da escrita da linha, levantamos a caneta e vamos para ela
            #2 Vai até o primeiro ponto da linha a escrever
            if (round(self.current_x, 1), round(self.current_y, 1)) != (round(x, 1), round(y, 1)):
                self.xy(x, y, wait=wait, interpolate=interpolate)

            # Pega as cordenadas do ponto final da linha e chama a função draw
            for point in line[1:]:
                x, y = point
                self.xy(x=x, y=y, wait=wait, interpolate=interpolate, draw=True)


    # Desenha 1 linha apenas passando o ponto inicial e final
    def draw_line(self, start=(0, 0), end=(0, 0), wait=0, interpolate=10):

        wait = wait or self.wait

        start_x, start_y = start
        end_x, end_y = end

        # Levanta a caneta e movimenta para o ponto inicial da linha
        self.pen.up()
        self.xy(x=start_x, y=start_y, wait=wait, interpolate=interpolate)

        # abaixa a caneta e movimenta (escrevendo) para o ponto final da linha
        self.pen.down()
        self.xy(x=end_x, y=end_y, wait=wait, interpolate=interpolate, draw=True)

        self.pen.up()


    # Movimenta a caneta para a posição específica.
    def xy(self, x=0, y=0, wait=0, interpolate=10, draw=False):

        wait = wait or self.wait

        # Sobe ou desce caneta
        if draw:
            self.pen.down()
        else:
            self.pen.up()

        # Converte posição x e y para angulos e Converte angulos para PWM
        (angle_1, angle_2) = self.xy_to_angles(x, y)
        (pulse_width_1, pulse_width_2) = self.angles_to_pw_1(angle_1), self.angles_to_pw_2(angle_2)

        # Se o PWM da posição q estamos for o memo para onde devemos ir, não faz nada, return
        if (pulse_width_1, pulse_width_2) == self.get_pulse_widths():

            # Garantir que a atual posição está atualizada
            self.current_x = x
            self.current_y = y
            return

        # Calcula a distância da pos atual para o ponto necessário
        # calculate how many steps we need for this move, and the x/y length of each
        (x_length, y_length) = (x - self.current_x, y - self.current_y)

        # Pega a distancia nominal entre os pontos (x1,y1) e (x2,y2)
        length = math.sqrt(x_length ** 2 + y_length **2)

        # Se foi defenido um número para interpolate, então criaremos X pontos entre a pos atual e o ponto necessário
        no_of_steps = int(length * interpolate) or 1

        # Salva tamanho dos mini passos que a caneta vai dar, serve para atualizar posição atual
        (length_of_step_x, length_of_step_y) = (x_length/no_of_steps, y_length/no_of_steps)

        for step in range(no_of_steps):
            
            # Salva nova posição com base na posição atual e a distância dos mini passos
            self.current_x = self.current_x + length_of_step_x
            self.current_y = self.current_y + length_of_step_y

            # calcula angulos da posição atual e salva eles
            angle_1, angle_2 = self.xy_to_angles(self.current_x, self.current_y)

            # Movimenta o motor para os angulos passados (posição que deve ir)
            self.set_angles(angle_1, angle_2)

            # incrementa o numero de passos dados e espera o tempo necessário para garantir precisão
            if step + 1 < no_of_steps:
                sleep(length * wait/no_of_steps)

        sleep(length * wait/10)

    # Movimenta o servo
    def set_angles(self, angle_1=0, angle_2=0):

        # Converte angulos para PWM
        pw_1, pw_2 = self.angles_to_pw_1(angle_1), self.angles_to_pw_2(angle_2)

        # Faz a adição da correção de histerese
        if pw_1 > self.previous_pw_1:
            self.active_hysteresis_correction_1 = self.hysteresis_correction_1
        elif pw_1 < self.previous_pw_1:
            self.active_hysteresis_correction_1 = - self.hysteresis_correction_1

        if pw_2 > self.previous_pw_2:
            self.active_hysteresis_correction_2 = self.hysteresis_correction_2
        elif pw_2 < self.previous_pw_2:
            self.active_hysteresis_correction_2 = - self.hysteresis_correction_2

        # Atualiza PWM atual
        self.previous_pw_1 = pw_1
        self.previous_pw_2 = pw_2

        # Enviando valor pwm com a correção de histerese definida pelos testes para os respectivos pinos de controle do motor
        self.rpi.set_servo_pulsewidth(14, pw_1 + self.active_hysteresis_correction_1)
        self.rpi.set_servo_pulsewidth(15, pw_2 + self.active_hysteresis_correction_2)

        # Atualizando angulos atuais e PWM atuais
        self.angle_1, self.angle_2 = angle_1, angle_2


    def angles_to_pw_1(self, angle):
        return (angle - self.arm_1_centre) * self.servo_1_degree_ms + self.servo_1_centre


    def angles_to_pw_2(self, angle):
        return (angle - self.arm_2_centre) * self.servo_2_degree_ms + self.servo_2_centre


    def get_pulse_widths(self):
        actual_pulse_width_1 = self.rpi.get_servo_pulsewidth(14)
        actual_pulse_width_2 = self.rpi.get_servo_pulsewidth(15)
        return (actual_pulse_width_1, actual_pulse_width_2)


    # Dado uma posição x/y, seja o ponto atual, ou um ponto que a caneta deverá ir. Convertemos o valor x/y para angulos de cada motor
    def xy_to_angles(self, x=0, y=0):

        hypotenuse = math.sqrt(x**2+y**2)

        if hypotenuse > self.INNER_ARM + self.OUTER_ARM:
            raise Exception(f"Cannot reach {hypotenuse}; total arm length is {self.INNER_ARM + self.OUTER_ARM}")

        hypotenuse_angle = math.asin(x/hypotenuse)

        inner_angle = math.acos(
            (hypotenuse**2+self.INNER_ARM**2-self.OUTER_ARM**2)/(2*hypotenuse*self.INNER_ARM)
        )
        outer_angle = math.acos(
            (self.INNER_ARM**2+self.OUTER_ARM**2-hypotenuse**2)/(2*self.INNER_ARM*self.OUTER_ARM)
        )

        shoulder_motor_angle = hypotenuse_angle - inner_angle
        elbow_motor_angle = math.pi - outer_angle

        return (math.degrees(shoulder_motor_angle), math.degrees(elbow_motor_angle))


class Pen:

    def __init__(self, vp, pw_up=1700, pw_down=1300, pin=18, transition_time=0.25):

        self.vp = vp
        self.pin = pin
        self.pw_up = pw_up
        self.pw_down = pw_down
        self.transition_time = transition_time
        self.rpi = pigpio.pi()
        self.rpi.set_PWM_frequency(self.pin, 50)

        self.up()
        sleep(0.3)
        self.down()
        sleep(0.3)
        self.up()
        sleep(0.3)

    def down(self):
        self.rpi.set_servo_pulsewidth(self.pin, self.pw_down)
        sleep(self.transition_time)

    def up(self):
        self.rpi.set_servo_pulsewidth(self.pin, self.pw_up)
        sleep(self.transition_time)
