# Docker Images for Python Barcode Detection on ARM64

This repository provides a guide on how to use the Dynamsoft Barcode Reader Python SDK (`dynamsoft-barcode-reader-bundle`) within Docker containers designed for the ARM64 architecture.

## Building the Docker Image for ARM64

To build the Docker image for ARM64, execute the following commands:

```bash
docker run --rm --privileged multiarch/qemu-user-static:register --reset
docker build --platform linux/arm64 -f DockerfileArm64 -t <IMAGE-NAME> .
```

## Running Python Barcode Detection in a Docker Container

To run barcode detection using the Python script inside a Docker container, mount the sample project and pass the image folder to the script:

```bash
docker run --platform linux/arm64 -it --rm -v $(pwd)/../../..:/usr/src/myapp -w /usr/src/myapp/examples/official/arm64 <IMAGE-NAME> python pillow_test.py /usr/src/myapp/images
```

You can also pass `.` to decode the images in the mounted folder itself.
