// Photocentre bench: turns the two-LED arm at a slow, constant rate.
// Hardware: Arduino Nano + 28BYJ-48 stepper + ULN2003 driver (IN1..IN4 -> D8..D11).
// The LEDs ride on the arm with their own battery, so no slip ring is needed.
// Dim the LEDs with resistors/trimmers, NOT with PWM: PWM flicker beats with the camera's
// rolling shutter and moves the photocentre.
#include <Stepper.h>
const int STEPS_PER_REV = 2048;      // 28BYJ-48 in full-step mode
const int RPM = 4;                   // ~15 s per turn -> ~450 video frames per turn at 30 fps
Stepper motor(STEPS_PER_REV, 8, 10, 9, 11);
void setup() { motor.setSpeed(RPM); }
void loop() { motor.step(1); }       // one step at a time keeps the motion smooth
