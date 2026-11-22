# Docker Images for Python Barcode Detection on ARM64 and ARM32
This repository provides a guide on how to use the Dynamsoft Barcode Reader Python SDK within Docker containers designed for ARM64 and ARM32 architectures.

## Building Docker Images for ARM64 and ARM32

To build Docker images for ARM64 and ARM32, execute the following commands:

```bash
docker run --rm --privileged multiarch/qemu-user-static:register --reset
docker build --platform linux/arm64 -f DockerfileArm64 -t <IMAGE-NAME> .
docker build --platform linux/arm/v7 -f DockerfileArm32 -t <IMAGE-NAME> .  
```

## Running Python Barcode Detection in Docker Containers

To run barcode detection using the Python script inside a Docker container, use these commands:

```bash
docker run --platform linux/arm64 -it --rm -v ${pwd}:/usr/src/myapp -w /usr/src/myapp <IMAGE-NAME> python pillow_test.py
docker run --platform linux/arm/v7 -it --rm -v ${pwd}:/usr/src/myapp -w /usr/src/myapp <IMAGE-NAME> python pillow_test.py
```

**Try the Pre-built Images**

You can also try the pre-built images directly:

```bash
docker run --platform linux/arm64 -it --rm -v ${pwd}:/usr/src/myapp -w /usr/src/myapp yushulx/dbr-arm64:1.0 python pillow_test.py
docker run --platform linux/arm/v7 -it --rm -v ${pwd}:/usr/src/myapp -w /usr/src/myapp yushulx/dbr-arm32:1.0 python pillow_test.py
```

## Emulating Raspberry Pi
Use [dockerpi](https://github.com/lukechilds/dockerpi) to test the performance of the Python Barcode SDK on Raspberry Pi emulators:

```bash
docker run -it lukechilds/dockerpi pi2
docker run -it lukechilds/dockerpi pi3
```

## Blog
[A Guide to Running ARM32 and ARM64 Python Barcode Readers in Docker Containers](https://www.dynamsoft.com/codepool/docker-arm64-arm32-python-barcode-qr-recognition.html)
