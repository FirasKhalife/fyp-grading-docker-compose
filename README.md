
# FYP Grading: Docker Compose

This repository contains Docker Compose configurations for setting up the environment for the FYP Grading project. 
Included is a shell script `docker-compose.sh` which serves as a convenient way to run Docker Compose commands 
that include all _**docker-compose.X.yml**_ files in the _**docker-compose**_ directory. 
This setup provides a robust framework for running a complex multi-service architecture with Docker Compose, 
facilitating easy development and deployment processes.

## Directory Structure Overview:
- **docker-compose.sh** - Shell script to run Docker Compose with all docker-compose files included.
- **docker-compose/** - Folder containing all docker-compose YAML files for individual services, as well as the following:
  - **config/** - Configuration files for different services.
  - **.env** - Local and non-sensitive environment variables for Docker Compose. Verify its contents and modify it if necessary to suit your local environment or deployment settings.
  - **common.yml** Common configuration inherited by multiple Docker services. 

## Using the `docker-compose.sh` Script:
The `docker-compose.sh` script is designed to simplify the execution of Docker Compose for the entire project. 
It automatically includes all the Docker Compose files in the command, so is an alias for the regular **docker-compose** command. 
Use it as the regular command, such as the following:

### To start all services:
```bash
./docker-compose.sh up
```
Append **-d** for detached mode.

### To start a specific service:
```bash
./docker-compose.sh up <service-name>
```
Append **-d** for detached mode.

### To stop services:
```bash
./docker-compose.sh down
```

### To view the whole compiled docker-compose file:
```bash
./docker-compose.sh config
```

## Important Notes:
- Make sure to run the script from the root directory of this repository, in a Unix-based environment.
- Ensure that the script has executable permissions:
```bash
chmod +x docker-compose.sh
```
