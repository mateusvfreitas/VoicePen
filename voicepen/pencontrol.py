# coding=utf-8

'''
tamanho dos bracos
braco outer arm, antebraco inner arm = 8 cm cada
caneta inicializando em (-8, 8)
angulo entre braco e ombro = -90
angulo ante antebraco e braco - 90
servo da caneta - up = 90; down = 45

layout
servo ombro = gpio 14
servo cotovelo = gpio 15
servo caneta = gpio 18
alcances dos servos = de 500 a 2500 us

pegar infos importantes da classe brachiograph e criar a classe voicepen

servo 1 = ombro
servo 2 = cotovelo
servo 3 = caneta
inner arm = braço
outer arm = antebraco

a fazer:
arquivo aponta para diretorio de fontes, se nao tem que instalar
de que tamanho fica o quadrado na hora de escrever
voltar a ouvir apos a escrita,
fazer ele iniciar sem senha

acho que na secao de plot file/ plot lines tem tudo o que precisa

The system uses centimetres as its basic unit of length. 8cm arms are suitable for drawing an area approximately 14cm wide by 9cm high. This fits well onto a sheet of A5 paper. (See Understanding the plotter’s geometry and How to optimise your plotter’s geometry and drawing area.)

sudo pigpiod && source env/bin/activate && cd BrachioGraph && python

acho que tem que remover tudo com virtual mode

ESSENCIAL PRA DESENHAR:
plot_file
    plot_lines

xy
    angles_to_xy


atributos e metodos desnecessarios:



Class Brachiograph   
__init__                    o      class Pen, rpi.set_PWM_frequency, rpi.set_servo_pulsewidth, angles_to_pw_1, angles_to_pw_2
plot_file                   o      plot_lines
plot_lines                  o      draw, xy, rotate_and_scale_lines (?), park (?), tqdm (?)
draw_line                   +      pen.up, pen.down, xy, draw
draw                        o      xy 
rotate_and_scale_lines      ?      analyse_lines
analyse_lines               ?
test_pattern                -      draw, xy, park, tqdm
vertical_lines              -      draw_line, park
horizontal_lines            -      draw_line, park
grid_lines                  -      vertical_lines, horizontal_lines
box                         -      draw, xy, park, tqdm
xy                          o      draw, Pen.up, Pen.down, xy_to_angles, angles_to_pulse_widths
                                   get_pulse_widths, set_angles
set_angles                  o      angles_to_pulse_widths, set_pulse_widths,
#  ----------------- angles-to-pulse-widths methods -----------------
naive_angles_to_pulse_widths_1  + 
naive_angles_to_pulse_widths_2  +
angles_to_pulse_widths      +      angles_to_pw_1, angles_to_pw_2
#  ----------------- hardware-related methods -----------------
set_pulse_widths            +      rpi.set_servo_pulsewidth, angles_to_pw_1, angles_to_pw_2
get_pulse_widths            +      rpi.get_servo_pulsewidth
park                        -      Pen.up, xy
quiet                       -      rpi.set_servo_pulsewidth
# ----------------- trigonometric methods -----------------
xy_to_angles                +      
angles_to_xy                -      
# ----------------- calibration -----------------
calibrate                   -      rpi.set_servo_pulsewidth, readchar
# ----------------- manual driving methods -----------------
drive                       -      set_pulse_widths, readchar
drive_xy                    -      readchar, xy
# ----------------- reporting methods -----------------
report                      -      get_pulse_widths
reset_report                -      

Class Pen
__init__                    +      rpi = pigpio.pi, rpi.set_PWM_frequency, up, down
down                        +       rpi.set_servo_pulsewidth
up                          +       rpi.set_servo_pulsewidth
pw                          -       rpi.set_servo_pulsewidth
calibrate                   -       bg.get_pulse_widths, bg.set_pulse_widths, readchar




'''



from time import sleep
import math
import numpy
import json

try:
    import pigpio
    force_virtual_mode = False
except ModuleNotFoundError:
    print("pigpio not installed, running in test mode")
    force_virtual_mode = True

import tqdm


class BrachioGraph:

    def __init__(
        self,
        inner_arm=8,                # Tamanho do braço (cm)
        outer_arm=8,                # Tamanho do antebraço (cm)
        servo_1_centre=1500,        # Angulo inicial do Ombro
        servo_2_centre=1500,        # Angulo inicial do Antebraço
        servo_1_degree_ms=-10,      # PWM relativo a 1 grau  # tweked
        servo_2_degree_ms=10,       # PWM relativo a 1 grau  # tweked
        arm_1_centre=-60,           # ???
        arm_2_centre=90,            # ???
        hysteresis_correction_1=0,  # Angulo de compensação para a Histerese  # tweked
        hysteresis_correction_2=0,  # Angulo de compensação para a Histerese  # tweked
        bounds=[-8, 4, 6, 13],      # Area máxima de desenho permitida (Retangulo)
        wait=None,                  # Fator de tempo de espera entre movimentos para melhorar precisão
        virtual_mode = False,       # Para debugar sem hardware
        pw_up=1500,                 # Angulo OFF do motor on/off
        pw_down=1100,               # Angulo ON do motor on/off
    ):

        # Salvando parametros default ou iniciados para a classe
        self.INNER_ARM = inner_arm
        self.OUTER_ARM = outer_arm

        ################# TIRAR
        self.virtual_mode = virtual_mode or force_virtual_mode
        #################

        self.bounds = bounds

        self.servo_1_centre = servo_1_centre
        self.servo_1_degree_ms = servo_1_degree_ms
        self.arm_1_centre = arm_1_centre
        self.hysteresis_correction_1 = hysteresis_correction_1

        self.servo_2_centre = servo_2_centre
        self.servo_2_degree_ms = servo_2_degree_ms
        self.arm_2_centre = arm_2_centre
        self.hysteresis_correction_2 = hysteresis_correction_2


        # Salva a função a ser chamada para o cálculo de Angulo para PWM
        self.angles_to_pw_1 = self.naive_angles_to_pulse_widths_1
        self.angles_to_pw_2 = self.naive_angles_to_pulse_widths_2


        # create the pen object, and make sure the pen is up
        self.pen = Pen(bg=self, pw_up=pw_up, pw_down=pw_down, virtual_mode=self.virtual_mode)

        ################## TIRAR
        if self.virtual_mode:

            print("Initialising virtual BrachioGraph")

            self.virtual_pw_1 = self.angles_to_pw_1(-90)
            self.virtual_pw_2 = self.angles_to_pw_2(90)

            # by default in virtual mode, we use a wait factor of 0 for speed
            self.wait = wait or 0

            print("    Pen is up")
            print("    Pulse-width 1", self.virtual_pw_1)
            print("    Pulse-width 2", self.virtual_pw_2)

        else:
        ##################
            # Cria instancia do Raspberry Pi
            self.rpi = pigpio.pi()

            # Limitando PWM dos motores para não ser maior que 100Hz para não queimar os servos
            self.rpi.set_PWM_frequency(14, 50)
            self.rpi.set_PWM_frequency(15, 50)

            # Leva os servos para seu centro
            self.rpi.set_servo_pulsewidth(14, self.angles_to_pw_1(-90))
            sleep(0.3)
            self.rpi.set_servo_pulsewidth(15, self.angles_to_pw_2(90))
            sleep(0.3)

            # Fator de tempo de espera entre movimentos para melhorar precisão, 0.1 como default
            self.wait = wait or .1


        # Setando a posição atual da caneta (já que mandamos os motores para o centro)
        self.current_x = -self.INNER_ARM
        self.current_y = self.OUTER_ARM

        ############### TIRAR (???)  reset_report
        self.angle_1 = self.angle_2 = None

        # Create sets for recording movement of the plotter.
        self.angles_used_1 = set()
        self.angles_used_2 = set()
        self.pulse_widths_used_1 = set()
        self.pulse_widths_used_2 = set()
        ############### TIRAR


        ############################## usado apenas na função set angles (?? funcionamento ??)
        self.previous_pw_1 = self.previous_pw_2 = 0
        self.active_hysteresis_correction_1 = self.active_hysteresis_correction_2 = 0
        ##############################


    # ----------------- drawing methods -----------------


    def plot_file(self, filename="", wait=0, interpolate=10, bounds=None):

        wait = wait or self.wait
        bounds = bounds or self.bounds

        if not bounds:
            return "File plotting is only possible when BrachioGraph.bounds is set."

        with open(filename, "r") as line_file:
            lines = json.load(line_file)

        self.plot_lines(lines=lines, wait=wait, interpolate=interpolate, bounds=bounds, flip=True)


    def plot_lines(self, lines=[], wait=0, interpolate=10, rotate=False, flip=False, bounds=None):

        wait = wait or self.wait
        bounds = bounds or self.bounds

        if not bounds:
            return "Line plotting is only possible when BrachioGraph.bounds is set."

        lines = self.rotate_and_scale_lines(lines=lines, bounds=bounds, flip=True)

        # Começa o processo de escrita, linha por linha e mostra barra de progresso com tdqm
        for line in tqdm.tqdm(lines, desc="Lines", leave=False):
            x, y = line[0]

            # Se não estamos dentro de 1mm para início da escrita da linha, levantamos a caneta e vamos para ela
            #2 Vai até o primeiro ponto da linha a escrever
            if (round(self.current_x, 1), round(self.current_y, 1)) != (round(x, 1), round(y, 1)):
                self.xy(x, y, wait=wait, interpolate=interpolate)

            # For feito apenas para o tdqm mostrar a barrinha de progresso, poderia não ter
            # Pega as cordenadas do ponto final da linha e chama a função draw
            for point in tqdm.tqdm(line[1:], desc="Segments", leave=False):
                x, y = point
                self.draw(x, y, wait=wait, interpolate=interpolate)

        self.park()

    # Desenha 1 linha apenas passando o ponto inicial e final
    def draw_line(self, start=(0, 0), end=(0, 0), wait=0, interpolate=10, both=False):

        wait = wait or self.wait

        start_x, start_y = start
        end_x, end_y = end

        self.pen.up()
        self.xy(x=start_x, y=start_y, wait=wait, interpolate=interpolate)

        self.pen.down()
        self.draw(x=end_x, y=end_y, wait=wait, interpolate=interpolate)

        if both:
            self.draw(x=start_x, y=start_y, wait=wait, interpolate=interpolate)

        self.pen.up()

    def draw(self, x=0, y=0, wait=0, interpolate=10):

        wait = wait or self.wait

        self.xy(x=x, y=y, wait=wait, interpolate=interpolate, draw=True)

    # ----------------- line-processing methods -----------------

    # Chama analyse_lines para verificar e pegar parametros para caber a imagem certo na area de impressao
    # Usa esses parametros para alterar a base de linhas atuais
    def rotate_and_scale_lines(self, lines=[], rotate=False, flip=False, bounds=None):

        rotate, x_mid_point, y_mid_point, box_x_mid_point, box_y_mid_point, divider = self.analyse_lines(
            lines=lines, rotate=rotate, bounds=bounds
        )

        for line in lines:
            for point in line:
                if rotate:
                    point[0], point[1] = point[1], point[0]

                x = point[0]
                x = x - x_mid_point         # shift x values so that they have zero as their mid-point
                x = x / divider             # scale x values to fit in our box width
                x = x + box_x_mid_point     # shift x values so that they have the box x midpoint as their endpoint

                if flip ^ rotate:
                    x = -x

                y = point[1]
                y = y - y_mid_point
                y = y / divider
                y = y + box_y_mid_point

                point[0], point[1] = x, y

        return lines

    # Faz os calculos loucos para saber se a imagem esta de acordo com a area de impressao, se nao, gera variaveis para caber a imagem na area
    # TENTAMOS FAZER SEM E DELETAMOS ISSO AQUI DAI
    def analyse_lines(self, lines=[], rotate=False, bounds=None):

        # lines is a tuple itself containing a number of tuples, each of which contains a number of 2-tuples
        #
        # [                                                                                     # |
        #     [                                                                                 # |
        #         [3, 4],                               # |                                     # |
        #         [2, 4],                               # |                                     # |
        #         [1, 5],  #  a single point in a line  # |  a list of points defining a line   # |
        #         [3, 5],                               # |                                     # |
        #         [3, 7],                               # |                                     # |
        #     ],                                                                                # |
        #     [                                                                                 # |  all the lines
        #         [...],                                                                        # |
        #         [...],                                                                        # |
        #     ],                                                                                # |
        #     [                                                                                 # |
        #         [...],                                                                        # |
        #         [...],                                                                        # |
        #     ],                                                                                # |
        # ]                                                                                     # |

        # First, we create a pair of empty sets for all the x and y values in all of the lines of the plot data.

        x_values_in_lines = set()
        y_values_in_lines = set()

        # Loop over each line and all the points in each line, to get sets of all the x and y values:

        for line in lines:

            x_values_in_line, y_values_in_line = zip(*line)

            x_values_in_lines.update(x_values_in_line)
            y_values_in_lines.update(y_values_in_line)

        # Identify the minimum and maximum values.

        min_x, max_x = min(x_values_in_lines), max(x_values_in_lines)
        min_y, max_y = min(y_values_in_lines), max(y_values_in_lines)

        # Identify the range they span.

        x_range, y_range = max_x - min_x, max_y - min_y
        box_x_range, box_y_range = bounds[2] - bounds[0], bounds[3] - bounds[1]

        # And their mid-points.

        x_mid_point, y_mid_point = (max_x + min_x) / 2, (max_y + min_y) / 2
        box_x_mid_point, box_y_mid_point = (bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2

        # Get a 'divider' value for each range - the value by which we must divide all x and y so that they will
        # fit safely inside the drawing range of the plotter.

        # If both image and box are in portrait orientation, or both in landscape, we don't need to rotate the plot.

        if (x_range >= y_range and box_x_range >= box_y_range) or (x_range <= y_range and box_x_range <= box_y_range):

            divider = max((x_range / box_x_range), (y_range / box_y_range))
            rotate = False

        else:

            divider = max((x_range / box_y_range), (y_range / box_x_range))
            rotate = True
            x_mid_point, y_mid_point = y_mid_point, x_mid_point

        return rotate, x_mid_point, y_mid_point, box_x_mid_point, box_y_mid_point, divider

    # ----------------- pen-moving methods -----------------

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
        (pulse_width_1, pulse_width_2) = self.angles_to_pulse_widths(angle_1, angle_2)

        # Se o PWM da posição q estamos for o memo para onde devemos ir, não faz nada, return
        if (pulse_width_1, pulse_width_2) == self.get_pulse_widths():

            # Garantir que a atual posição está atualizada
            self.current_x = x
            self.current_y = y

            return

        ############# ?? we assume the pantograph knows its x/y positions - if not, there could be
        ############# ?? a sudden movement later

        # Calcula a distância da pos atual para o ponto necessário
        # calculate how many steps we need for this move, and the x/y length of each
        (x_length, y_length) = (x - self.current_x, y - self.current_y)

        # Pega a distancia nominal entre os pontos (x1,y1) e (x2,y2)
        length = math.sqrt(x_length ** 2 + y_length **2)

        # Se foi defenido um número para interpolate, então criaremos X pontos entre a pos atual e o ponto necessário
        no_of_steps = int(length * interpolate) or 1

        ############### TIRAR ?????
        if no_of_steps < 100:
            disable_tqdm = True
        else:
            disable_tqdm = False
        ###############

        # Salva tamanho dos mini passos que a caneta vai dar, serve para atualizar posição atual
        (length_of_step_x, length_of_step_y) = (x_length/no_of_steps, y_length/no_of_steps)

        # Para cada passo no numero de passos necessários, tirar?? -> TDQM safado de novo aqui
        for step in tqdm.tqdm(range(no_of_steps), desc='Interpolation', leave=False, disable=disable_tqdm):
            
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

    # MOVIMENTA O SERVO
    def set_angles(self, angle_1=0, angle_2=0):

        # Converte angulos para PWM
        pw_1, pw_2 = self.angles_to_pulse_widths(angle_1, angle_2)

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

        ########### Substituir sa porra, PRA QUE??
        self.set_pulse_widths(pw_1 + self.active_hysteresis_correction_1, pw_2 + self.active_hysteresis_correction_2)
        ########### Substituir sa porra pelo conteúdo dessa função aqui ^^

        # Atualizando angulos atuais e PWM atuais
        self.angle_1, self.angle_2 = angle_1, angle_2

        ############# TIRAR
        self.angles_used_1.add(int(angle_1))
        self.angles_used_2.add(int(angle_2))
        self.pulse_widths_used_1.add(int(pw_1))
        self.pulse_widths_used_2.add(int(pw_2))
        ############# FOUDA-SE pra que quero saber todos os caminhos e angulos usados?


    #  ----------------- angles-to-pulse-widths methods -----------------

    def naive_angles_to_pulse_widths_1(self, angle):
        return (angle - self.arm_1_centre) * self.servo_1_degree_ms + self.servo_1_centre

    def naive_angles_to_pulse_widths_2(self, angle):
        return (angle - self.arm_2_centre) * self.servo_2_degree_ms + self.servo_2_centre


    def angles_to_pulse_widths(self, angle_1, angle_2):
        # Given a pair of angles, returns the appropriate pulse widths.

        # at present we assume only one method of calculating, using the angles_to_pw_1 and angles_to_pw_2
        # functions created using numpy

        pulse_width_1, pulse_width_2 = self.angles_to_pw_1(angle_1), self.angles_to_pw_2(angle_2)

        return (pulse_width_1, pulse_width_2)


    #  ----------------- hardware-related methods -----------------

    def set_pulse_widths(self, pw_1, pw_2):

        if self.virtual_mode:

            if (500 < pw_1 < 2500) and (500 < pw_2 < 2500):

                self.virtual_pw_1 = self.angles_to_pw_1(pw_1)
                self.virtual_pw_2 = self.angles_to_pw_2(pw_2)

            else:
               raise ValueError

        else:

            self.rpi.set_servo_pulsewidth(14, pw_1)
            self.rpi.set_servo_pulsewidth(15, pw_2)


    def get_pulse_widths(self):

        if self.virtual_mode:

            actual_pulse_width_1 = self.virtual_pw_1
            actual_pulse_width_2 = self.virtual_pw_2

        else:

            actual_pulse_width_1 = self.rpi.get_servo_pulsewidth(14)
            actual_pulse_width_2 = self.rpi.get_servo_pulsewidth(15)

        return (actual_pulse_width_1, actual_pulse_width_2)


    # ----------------- trigonometric methods -----------------

    # Every x/y position of the plotter corresponds to a pair of angles of the arms. These methods
    # calculate:
    #
    # the angles required to reach any x/y position
    # the x/y position represented by any pair of angles

    def xy_to_angles(self, x=0, y=0):

        # convert x/y co-ordinates into motor angles

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

    def __init__(self, bg, pw_up=1700, pw_down=1300, pin=18, transition_time=0.25, virtual_mode=False):

        self.bg = bg
        self.pin = pin
        self.pw_up = pw_up
        self.pw_down = pw_down
        self.transition_time = transition_time
        self.virtual_mode = virtual_mode
        if self.virtual_mode:

            print("Initialising virtual Pen")

        else:

            self.rpi = pigpio.pi()
            self.rpi.set_PWM_frequency(self.pin, 50)

        self.up()
        sleep(0.3)
        self.down()
        sleep(0.3)
        self.up()
        sleep(0.3)


    def down(self):

        if self.virtual_mode:
            self.virtual_pw = self.pw_down

        else:
            self.rpi.set_servo_pulsewidth(self.pin, self.pw_down)
            sleep(self.transition_time)


    def up(self):

        if self.virtual_mode:
            self.virtual_pw = self.pw_up

        else:
            self.rpi.set_servo_pulsewidth(self.pin, self.pw_up)
            sleep(self.transition_time)






brachio = BrachioGraph()
brachio.plot_file(filename=r"C:\Users\Thiago\Desktop\Oficinas\VoicePen\text.json")