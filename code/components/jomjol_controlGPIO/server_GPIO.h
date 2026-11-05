#pragma once

#ifndef SERVER_GPIO_H
#define SERVER_GPIO_H

#include <esp_log.h>

#include <esp_http_server.h>
#include <map>
#include "driver/gpio.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"

#include "SmartLeds.h"

typedef enum {
    GPIO_PIN_MODE_DISABLED              = 0x0,
    GPIO_PIN_MODE_INPUT                 = 0x1,
    GPIO_PIN_MODE_INPUT_PULLUP          = 0x2,
    GPIO_PIN_MODE_INPUT_PULLDOWN        = 0x3,
    GPIO_PIN_MODE_OUTPUT                = 0x4,
    GPIO_PIN_MODE_BUILT_IN_FLASH_LED    = 0x5,
    GPIO_PIN_MODE_OUTPUT_PWM            = 0x6,
    GPIO_PIN_MODE_EXTERNAL_FLASH_PWM    = 0x7,
    GPIO_PIN_MODE_EXTERNAL_FLASH_WS281X = 0x8,
    GPIO_PIN_MODE_SERVO                 = 0x9,
} gpio_pin_mode_t;

struct GpioResult {
    gpio_num_t gpio;
    int value;
};

typedef enum {
    GPIO_SET_SOURCE_INTERNAL  = 0,
    GPIO_SET_SOURCE_MQTT  = 1,
    GPIO_SET_SOURCE_HTTP  = 2,
} gpio_set_source;

class GpioPin {
public:
    GpioPin(gpio_num_t gpio, const char* name, gpio_pin_mode_t mode, gpio_int_type_t interruptType, uint8_t dutyResolution, std::string mqttTopic, bool httpEnable);
    ~GpioPin();

    void init();
    bool getValue(std::string* errorText);
    void setValue(bool value, gpio_set_source setSource, std::string* errorText);
#ifdef ENABLE_MQTT
    bool handleMQTT(std::string, char* data, int data_len);
#endif //ENABLE_MQTT
    void publishState();
    void gpioInterrupt(int value);
    gpio_int_type_t getInterruptType() { return _interruptType; }
    gpio_pin_mode_t getMode() { return _mode; }
    gpio_num_t getGPIO(){return _gpio;};
    void setFlashDuty(int duty) { _flashDuty = duty; }
    void setServoParameter(int restAngle, int pressAngle, int pressDuration, int waitAfterPress, int displayOnTime);
    void servoPress(bool force);

private:
    bool isPwmFlash();
    void initGpio();
    void servoSetAngle(int angle);
    void servoStop();

    gpio_num_t _gpio;
    const char* _name;
    gpio_pin_mode_t _mode;
    gpio_int_type_t _interruptType;
    std::string _mqttTopic;
    int currentState = -1;
    int _flashDuty = -1;                // -1 = full brightness

    int _servoRestAngle = 0;
    int _servoPressAngle = 90;
    int _servoPressDuration = 500;      // ms
    int _servoWaitAfterPress = 1000;    // ms
    int _servoDisplayOnTime = 0;        // s, 0 = always press
    int64_t _servoLastRelease = -1;     // us since boot, -1 = never pressed
    SemaphoreHandle_t _servoMutex = NULL;
};

esp_err_t callHandleHttpRequest(httpd_req_t *req);
void taskGpioHandler(void *pvParameter);

class GpioHandler {
public:
    GpioHandler(std::string configFile, httpd_handle_t httpServer);
    ~GpioHandler();
    
    void init();
    void deinit();
    void registerGpioUri();
    esp_err_t handleHttpRequest(httpd_req_t *req);
    void taskHandler();
    void gpioInterrupt(GpioResult* gpioResult);  
    void flashLightEnable(bool value, int duty = -1);
    bool isEnabled() { return _isEnabled; }
    bool servoPress();
#ifdef ENABLE_MQTT
    void handleMQTTconnect();
#endif //ENABLE_MQTT

private:
    std::string _configFile;
    httpd_handle_t _httpServer;
    std::map<gpio_num_t, GpioPin*> *gpioMap = NULL;
    TaskHandle_t xHandleTaskGpio = NULL;
    bool _isEnabled = false;

    int LEDNumbers = 2;
    Rgb LEDColor = Rgb{ 255, 255, 255 };
    LedType LEDType = LED_WS2812;

    int ServoRestAngle = 0;
    int ServoPressAngle = 90;
    int ServoPressDuration = 500;       // ms
    int ServoWaitAfterPress = 1000;     // ms
    int ServoDisplayOnTime = 0;         // s
#ifdef __LEDGLOBAL
    SmartLed *leds_global = NULL;
#endif

    bool readConfig();
    void clear();
    
    gpio_num_t resolvePinNr(uint8_t pinNr);
    gpio_pin_mode_t resolvePinMode(std::string input);
    gpio_int_type_t resolveIntType(std::string input);
};

void gpio_handler_create(httpd_handle_t server);
void gpio_handler_init();
void gpio_handler_deinit();
void gpio_handler_destroy();
GpioHandler* gpio_handler_get();



#endif //SERVER_GPIO_H

