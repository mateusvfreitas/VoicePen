# coding=utf-8

from time import sleep
import math
import json
import pigpio

class VoicePen:
    def __init__(
        self,
        arm=8,                  # Arm size (cm)
        forearm=8,              # Forearm size (cm)
        arm_center=-45,         # Central arm angle
        forearm_center=90,      # Central forearm angle
        shoulder_center=1700,   # Central shoulder motor pulse width
        shoulder_pulse=-10,     # PW value that equals 1 degree for shoulder motor
        elbow_center=1500,      # Central elbow motor pulse width
        elbow_pulse=10,         # PW value that equals 1 degree for elbow motor
        pen_center=1500,        # central pen servo pulse width
        pen_up=1500,            # pulse width to raise pen
        pen_down=1100,          # pulse width to lower pen
        bounds=[-8, 6, 4, 12],  # Defining maximum plotting area = xi = -8, xf = 4, yi = 6, yf = 12
        wait=0.1,               # Wait factor to improve precision
        interpolate=100         # number of steps for each pen movement
    ):

        self.arm = arm
        self.forearm = forearm

        self.arm_center = arm_center
        self.forearm_center = forearm_center

        self.shoulder_center = shoulder_center
        self.shoulder_pulse = shoulder_pulse

        self.elbow_center = elbow_center
        self.elbow_pulse = elbow_pulse

        self.pen_center = pen_center
        self.pen_up = pen_up
        self.pen_down = pen_down

        self.bounds = bounds
        
        self.wait = wait
        self.interpolate = interpolate
        
        # create rpi instance
        self.rpi = pigpio.pi()

        # servomotors startup
        self.rpi.set_PWM_frequency(14, 50)
        self.rpi.set_PWM_frequency(15, 50)
        self.rpi.set_PWM_frequency(18, 50)

        # set starting pen position, raise, lower, raise pen
        self.rpi.set_servo_pulsewidth(14, self.shoulder_angle_to_pw(-90))
        sleep(0.5)
        self.rpi.set_servo_pulsewidth(15, self.elbow_angle_to_pw(90))
        sleep(0.5)
        self.rpi.set_servo_pulsewidth(18, self.pen_up)
        sleep(0.5)
        self.rpi.set_servo_pulsewidth(18, self.pen_down)
        sleep(0.5)
        self.rpi.set_servo_pulsewidth(18, self.pen_up)
        sleep(0.5)

        # for self reference
        self.current_x = -self.arm
        self.current_y = self.forearm
        self.shoulder_angle = self.elbow_angle = None
        self.previous_shoulder_pw = self.previous_elbow_pw = 0

    #
    def lower_pen(self):
        self.rpi.set_servo_pulsewidth(18, self.pen_down)
        sleep(0.5)

    #
    def raise_pen(self):
        self.rpi.set_servo_pulsewidth(18, self.pen_up)
        sleep(0.5)
    
    # loads json and draws based on lines
    def draw_from_file(self, filename=""):

        with open(filename, "r") as line_file:
            lines = json.load(line_file)

        for line in lines:
            x, y = line[0]

            # move pen to start point
            self.move_pen(x, y)

            for point in line[1:]:
                x, y = point
                self.move_pen(x=x, y=y, draw=True)
    
    # draws line based on startpoind and endpoint, used for testing
    def test_draw(self, start=(0, 0), end=(0, 0)):

        start_x, start_y = start
        end_x, end_y = end

        self.raise_pen()
        self.move_pen(x=start_x, y=start_y)

        self.lower_pen()
        self.move_pen(x=end_x, y=end_y, draw=True)

        self.raise_pen()

    # pen movement method: converts position into pulse width, generates number of steps to write each line, draws if draw is True
    def move_pen(self, x=0, y=0, draw=False):
        
        if draw:
            self.lower_pen()
        else:
            self.raise_pen()

        (shoulder_angle, elbow_angle) = self.coordinate_to_angle(x, y)
        (shoulder_pw, elbow_pw) = self.shoulder_angle_to_pw(shoulder_angle), self.elbow_angle_to_pw(elbow_angle)

        if (shoulder_pw, elbow_pw) == self.get_pulse_widths():

            self.current_x = x
            self.current_y = y
            return

        (delta_x, delta_y) = (x - self.current_x, y - self.current_y)

        length = math.sqrt(delta_x ** 2 + delta_y **2)

        steps = int(length * self.interpolate) or 1

        (step_x, step_y) = (delta_x/steps, delta_y/steps)

        # updates position and moves pen
        for step in range(steps):
            
            self.current_x = self.current_x + step_x
            self.current_y = self.current_y + step_y

            s_angle, e_angle = self.coordinate_to_angle(self.current_x, self.current_y)

            self.set_angles(s_angle, e_angle)

            if step + 1 < steps:
                sleep(self.wait/10)

        sleep(length * self.wait/10)

    # updates shoulder and elbow angles
    def set_angles(self, s_angle=0, e_angle=0):

        s_pw, e_pw = self.shoulder_angle_to_pw(s_angle), self.elbow_angle_to_pw(e_angle)
        
        self.previous_shoulder_pw = s_pw
        self.previous_elbow_pw = e_pw
        
        self.shoulder_angle, self.elbow_angle = s_angle, e_angle


    def shoulder_angle_to_pw(self, angle):

            return (angle - self.arm_center) * self.shoulder_pulse + self.shoulder_center

    def elbow_angle_to_pw(self, angle):

            return (angle - self.forearm_center) * self.elbow_pulse + self.elbow_pulse


    def set_pulse_widths(self, s_pw, e_pw):

        self.rpi.set_servo_pulsewidth(14, s_pw)
        self.rpi.set_servo_pulsewidth(15, e_pw)


    def get_pulse_widths(self):

        current_shoulder_pulse = self.rpi.get_servo_pulsewidth(14)
        current_elbow_pulse = self.rpi.get_servo_pulsewidth(15)
        return (current_shoulder_pulse, current_elbow_pulse)


    def coordinate_to_angle(self, x=0, y=0):

        hypotenuse = math.sqrt(x**2+y**2)

        if hypotenuse > self.arm + self.forearm:
            raise Exception(f"out of bounds: cannot reach distance greater than 16")

        theta = math.asin(x/hypotenuse)
        alpha = math.acos((hypotenuse**2+self.arm**2-self.forearm**2)/(2*hypotenuse*self.arm))
        beta = math.acos((self.arm**2+self.forearm**2-hypotenuse**2)/(2*self.arm*self.forearm))

        shoulder_servo_angle = theta - alpha
        elbow_servo_angle = math.pi - beta

        return (math.degrees(shoulder_servo_angle), math.degrees(elbow_servo_angle))

vp = VoicePen()
sleep(0.5)
vp.test_draw(start=(vp.bounds[0], vp.bounds[1]),end=(vp.bounds[0], vp.bounds[3]))
sleep(0.1)
vp.test_draw(start=(vp.bounds[0], vp.bounds[3]),end=(vp.bounds[2], vp.bounds[3]))
sleep(0.1)
vp.test_draw(start=(vp.bounds[2], vp.bounds[3]),end=(vp.bounds[2], vp.bounds[1]))
sleep(0.1)
vp.test_draw(start=(vp.bounds[2], vp.bounds[1]),end=(vp.bounds[0], vp.bounds[1]))
sleep(0.1)
vp.test_draw(start=(vp.bounds[0], vp.bounds[1]),end=(vp.bounds[2], vp.bounds[3]))
sleep(0.1)
vp.move_pen(x=vp.bounds[0],y=vp.bounds[1])