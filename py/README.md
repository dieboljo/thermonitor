# Thermonitor
A TUI IoT sensor dashboard

### Steps to install:
- conda env create --file environment.yaml
- conda activate thermonitor
- python3 -m pip install .
- python3 -m pip show thermonitor
- binary is located in 'bin' folder of thermonitor env (sibling to 'lib' folder above)
- symlink binary from step above to path, or add to path
- OPTIONAL: run aviader server (`node app.js` in weather service folder)
- thermonitor

### Docker:
- docker build --tag thermonitor
- docker run -ti thermonitor:latest
