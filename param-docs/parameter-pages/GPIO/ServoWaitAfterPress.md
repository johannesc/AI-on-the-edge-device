# Parameter `ServoWaitAfterPress`
Default Value: `1000`

!!! Warning
    This is an **Expert Parameter**! Only change it if you understand what it does!

Unit: Milliseconds

Time to wait after the button was released before the picture gets taken, e.g. until the display of the meter is switched on (only used if a GPIO is configured in `servo` mode, see `IO13` parameter).
At least 500 ms are always waited to let the servo return to its rest position.

!!! Note
    `WaitBeforeTakingPicture` (flash light on) is added after this time.
