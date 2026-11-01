# Parameter `ServoDisplayOnTime`
Default Value: `0`

!!! Warning
    This is an **Expert Parameter**! Only change it if you understand what it does!

Unit: Seconds

How long the display of the meter stays on after a button press (only used if a GPIO is configured in `servo` mode, see `IO13` parameter).
On many meters a press while the display is on switches to another screen (e.g. flow rate instead of the volume). If the last press was less than this time ago, the press before taking a picture is skipped.
Close to the end of this time (+/- 5 s), it waits until the display is surely off and presses then.

`0` = always press.

!!! Note
    A press triggered manually via MQTT or HTTP is always executed.
