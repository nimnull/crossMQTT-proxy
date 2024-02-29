# crossMQTT-proxy

mqtt proxy bridge

tested with mosquitto v2.0.11

# Development env
	make setup_dev
    make run_local

# Run release
    docker run nimnull/mqtt-bridge:latest -v ./config.yml:/opt/config.yaml
