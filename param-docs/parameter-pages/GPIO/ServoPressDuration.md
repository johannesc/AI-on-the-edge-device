# Parameter `ServoPressDuration`
Default Value: `500`

!!! Warning
    This is an **Expert Parameter**! Only change it if you understand what it does!

Unit: Milliseconds

Time the servo stays at `ServoPressAngle` before it returns to `ServoRestAngle` (only used if a GPIO is configured in `servo` mode, see `IO13` parameter).
This includes the time the servo needs to move to the press angle.

!!! Note
    Many meters distinguish short and long presses. E.g. on a Sagemcom Siconia water meter a press longer than 1.2 s switches to another menu, so keep the value well below that.
