from enum import Enum

class AstraTopics(Enum):
    # General communication topic for testing
    CHATTER_TOPIC = "/topic"
    # Core Control Topics
    CORE_FEEDBACK = "/astra/core/feedback"
    CORE_CONTROL = "/astra/core/control"
    # Rover Connection Status Service
    CORE_PING = "/astra/core/ping"
    
    ARM_FEEDBACK = "/astra/arm/feedback"
    ARM_CONTROL = '/astra/arm/control'
    ARM_COMMAND = '/astra/arm/command'

    BIO_FEEDBACK = '/astra/bio/feedback'
    BIO_CONTROL = '/astra/bio/control'
    FAERIE_FEEDBACK = '/astra/arm/bio/feedback'
    FAERIE_CONTROL = '/astra/arm/bio/control'

    AUTO_FEEDBACK = '/astra/auto/feedback'