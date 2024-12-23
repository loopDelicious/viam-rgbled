import asyncio
from typing import Any, ClassVar, Final, Mapping, Optional, Sequence, cast

from typing_extensions import Self
from viam.components.generic import *
from viam.module.module import Module
from viam.proto.app.robot import ComponentConfig
from viam.proto.common import ResourceName
from viam.resource.base import ResourceBase
from viam.resource.easy_resource import EasyResource
from viam.resource.types import Model, ModelFamily
from viam.utils import struct_to_dict
from viam.components.board import Board


class Rgbled(Generic, EasyResource):
    MODEL: ClassVar[Model] = Model(ModelFamily("joyce", "led"), "rgbled")

    @classmethod
    def new(
        cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ) -> Self:
        """This method creates a new instance of this RGB LED component.
        """
        return super().new(config, dependencies)

    @classmethod
    def validate_config(cls, config: ComponentConfig) -> Sequence[str]:
        """This method allows you to validate the configuration object received from the machine,
        as well as to return any implicit dependencies based on that `config`.
        """
        fields = config.attributes.fields

        for pin in ["green_pin", "red_pin", "blue_pin"]:
            if pin in fields:
                if not fields[pin].HasField("string_value"):
                    raise Exception(f"{pin} must be configured as a string.")
                if not fields[pin].string_value.isdigit():
                    raise Exception(f"{pin} must be a string containing only digits.")

        if "board" in fields:
            if not fields["board"].HasField("string_value"):
                raise Exception("Board name must be configured as a string.")

        return []

    def reconfigure(
        self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ):
        """This method allows you to dynamically update your service when it receives a new `config` object.
        """
        attrs = struct_to_dict(config.attributes)

        self.green_pin = attrs.get("green_pin")
        self.red_pin = attrs.get("red_pin")
        self.blue_pin = attrs.get("blue_pin")

        self.board = attrs.get("board")
        self.logger.debug("Using board: " + str(self.board))
        boardResourceName = Board.get_resource_name(self.board)
        self.board = dependencies.get(boardResourceName)
        if not isinstance(self.board, Board):
            raise Exception(f"Board '{boardResourceName}' not found during reconfiguration.")

        return super().reconfigure(config, dependencies)
    
    async def control_rgb_led(self, red: float, green: float, blue: float, duration: float = 1.0):
        """Control the RGB LED with specified intensity for each color."""
        try:
            if not (0.0 <= red <= 1.0):
                raise ValueError(f"Red intensity must be between 0 and 1. Got: {red}")
            if not (0.0 <= green <= 1.0):
                raise ValueError(f"Green intensity must be between 0 and 1. Got: {green}")
            if not (0.0 <= blue <= 1.0):
                raise ValueError(f"Blue intensity must be between 0 and 1. Got: {blue}")

            red_pin = await self.board.gpio_pin_by_name(name=self.red_pin)
            green_pin = await self.board.gpio_pin_by_name(name=self.green_pin)
            blue_pin = await self.board.gpio_pin_by_name(name=self.blue_pin)

            self.logger.info(f"Setting RGB LED: red={red}, green={green}, blue={blue}, duration={duration}")

            await red_pin.set_pwm(red)
            await green_pin.set_pwm(green)
            await blue_pin.set_pwm(blue)
            await asyncio.sleep(duration)

            # Turn off the LED after the duration
            await red_pin.set_pwm(0.0)
            await green_pin.set_pwm(0.0)
            await blue_pin.set_pwm(0.0)

            self.logger.info("RGB LED control completed successfully.")
        except Exception as e:
            self.logger.error(f"Error in control_rgb_led: {e}")
            raise
        
    async def do_command(
        self,
        command: dict[str, Any],
        *,
        timeout: Optional[float] = None,
        **kwargs
    ) -> dict[str, Any]:
        """Handle runtime commands for the RGB LED component."""
        result = {}

        for name, args in command.items():
            if name == "control_rgb_led":
                try:
                    red = args.get("red", 0.0)
                    green = args.get("green", 0.0)
                    blue = args.get("blue", 0.0)
                    duration = args.get("duration", 1.0)

                    await self.control_rgb_led(red=red, green=green, blue=blue, duration=duration)
                    result["control_rgb_led"] = f"RGB LED controlled with red={red}, green={green}, blue={blue} for {duration}s."
                except Exception as e:
                    self.logger.error(f"Error in do_command (control_rgb_led): {e}")
                    result["control_rgb_led"] = f"Error: {str(e)}"

            elif name == "ripple":
                try:
                    duration = args.get("duration", 5.0)
                    await self.ripple(duration=duration)
                    result["ripple"] = f"Ripple effect completed for duration={duration}s."
                except Exception as e:
                    self.logger.error(f"Error in do_command (ripple): {e}")
                    result["ripple"] = f"Error: {str(e)}"

            else:
                result[name] = f"Unknown command: {name}"

        return result
    
    async def ripple(self, duration: float = 5.0):
        """Create a ripple effect on the RGB LED with color changes and pulsating intensity."""
        try:
            red_pin = await self.board.gpio_pin_by_name(name=self.red_pin)
            green_pin = await self.board.gpio_pin_by_name(name=self.green_pin)
            blue_pin = await self.board.gpio_pin_by_name(name=self.blue_pin)

            self.logger.info(f"Starting ripple effect for duration={duration}")

            steps = 50
            for i in range(steps):
                cycle_time = duration / steps
                intensity = (1 - abs((i % (steps // 2)) / (steps // 4) - 1))
                red_intensity = intensity if i % 3 == 0 else 0
                green_intensity = intensity if i % 3 == 1 else 0
                blue_intensity = intensity if i % 3 == 2 else 0

                await red_pin.set_pwm(red_intensity)
                await green_pin.set_pwm(green_intensity)
                await blue_pin.set_pwm(blue_intensity)
                await asyncio.sleep(cycle_time)

            # Turn off the LEDs
            await red_pin.set_pwm(0.0)
            await green_pin.set_pwm(0.0)
            await blue_pin.set_pwm(0.0)

            self.logger.info("Ripple effect completed successfully.")
        except Exception as e:
            self.logger.error(f"Error in ripple: {e}")
            raise
    

if __name__ == "__main__":
    asyncio.run(Module.run_from_registry())