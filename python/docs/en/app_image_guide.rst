Application Image Build and Import Guide
=========================================

Overview
--------

This guide describes how to build an application Docker image in your development environment and import it onto an AIPC device for deployment.

The complete workflow includes:

#. Prepare application files (Dockerfile, app.py)
#. Build the Docker image
#. Export the image as a tar file
#. Import via the Web Console installation wizard, or use the command line

.. tip::

   The Web Console provides a graphical **Application Installation Wizard** that supports uploading image files and configuring application parameters step by step, without manually editing app.yaml or using SCP for file transfer. The Web Console method is recommended.

.. _app_image_step1:

Step 1: Prepare Application Files
----------------------------------

Create an application directory and prepare the following two core files. Application configuration (metadata, permissions, resources, etc.) will be filled in during the Web Console installation wizard.

Create Application Directory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   mkdir my-app && cd my-app

Application Code (app.py)
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   #!/usr/bin/env python3
   """My Application"""

   import signal
   import sys
   from hailo_ipc_sdk import InferenceClient, EventClient, DeviceClient, Config


   class MyApp:
       def __init__(self):
           self.running = True
           self.app_id = Config.get_app_id()

           self.inference = InferenceClient()
           self.events = EventClient()
           self.device = DeviceClient()

           signal.signal(signal.SIGINT, self.signal_handler)
           signal.signal(signal.SIGTERM, self.signal_handler)

       def signal_handler(self, signum, frame):
           self.running = False

       def run(self):
           try:
               for frame, result in self.inference.subscribe(
                   stream="cam0_main", model="person_v1", fps=10
               ):
                   if not self.running:
                       break
                   person_count = result.count_by_label("person")
                   if person_count > 0:
                       self.events.publish(f"app/{self.app_id}/detection", {
                           "count": person_count,
                       })
           except Exception as e:
               print(f"[{self.app_id}] Error: {e}")
           finally:
               self.inference.close()
               self.events.close()
               self.device.close()


   if __name__ == "__main__":
       MyApp().run()

Dockerfile
~~~~~~~~~~

.. code-block:: dockerfile

   FROM python:3.9-slim

   LABEL maintainer="your@email.com"

   # Install NE503 Python SDK from the public source repository.
   # PyPI packages are not published yet.
   RUN apt-get update \
       && apt-get install -y --no-install-recommends git \
       && rm -rf /var/lib/apt/lists/*
   RUN python -m pip install --no-cache-dir \
       "git+https://github.com/camthink-ai/ne503-aipc-sdks.git#subdirectory=python"

   WORKDIR /app
   COPY app.py app.yaml /app/

   RUN mkdir -p /app/logs /app/data

   # Non-root user (recommended)
   RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
   USER appuser

   ENV APP_ID=my_app
   ENV DEBUG=0
   ENV LOG_LEVEL=INFO

   HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
     CMD python3 -c "import sys; sys.exit(0)"

   CMD ["python3", "app.py"]

.. _app_image_step2:

Step 2: Build the Docker Image
-------------------------------

Run the build command in the application directory:

.. code-block:: bash

   docker build -t my-app:1.0.0 .

Build parameters:

- ``-t my-app:1.0.0`` — Image name and tag, must match ``spec.image`` in ``app.yaml``
- ``.`` — Build context is the current directory

Verify the image was built successfully:

.. code-block:: bash

   docker images | grep my-app

.. note::

   If the application requires additional dependencies, add a ``requirements.txt`` file to the directory and include ``RUN pip install -r requirements.txt`` in the Dockerfile. For offline or repeatable builds, build the SDK wheel first, copy ``hailo_ipc_sdk-*.whl`` into the image, and install that local wheel instead of installing from GitHub.

.. _app_image_step3:

Step 3: Export the Image
-------------------------

Export the built image as a tar file:

.. code-block:: bash

   docker save my-app:1.0.0 -o my-app.tar

It is recommended to use gzip compression to reduce transfer size:

.. code-block:: bash

   docker save my-app:1.0.0 | gzip > my-app.tar.gz

Compression comparison:

.. list-table::
   :header-rows: 1
   :widths: 25 30 30

   * - Format
     - Size
     - Compression Ratio
   * - tar
     - ~500MB
     - —
   * - tar.gz
     - ~150MB
     - ~70%
   * - tar.xz
     - ~100MB
     - ~80%

.. _app_image_step4:

Step 4: Web Console Import (Recommended)
-----------------------------------------

The Web Console provides a **6-step Application Installation Wizard** that supports uploading image files and configuring application parameters step by step.

.. note::

   Supported image file formats: ``.tar``, ``.tar.gz``, ``.tgz``, maximum 2GB.

Open the Installation Wizard
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Open a browser and navigate to the device Web Console: ``http://<device-ip>:8080``
#. Navigate to the **Application Management** page
#. Click the **Import Application** card to open the installation wizard

Wizard Steps
~~~~~~~~~~~~

**Step 1 — Select Image Source**

Choose one of the following methods:

- **Image Registry**: Enter the Docker image address (e.g., ``docker.io/library/nginx:latest``)
- **Upload Image**: Drag and drop or select a local image file (``.tar`` / ``.tar.gz`` / ``.tgz``), upload progress is displayed

**Step 2 — Basic Information**

Fill in application metadata:

- **Application ID**: Unique identifier (lowercase letters, numbers, hyphens)
- **Application Name**: Display name
- **Version**: Semantic version number (default ``1.0.0``)
- **Description**: Application functionality description

**Step 3 — Resource Configuration**

Set container resource limits and runtime options:

- **CPU Limit**: e.g., ``50%``
- **Memory Limit**: Select from dropdown (128Mi / 256Mi / 512Mi / 1Gi / 2Gi)
- **Shared Memory**: Enable for zero-copy video stream access
- **Auto Start**: Automatically run when the device boots
- **Restart Policy**: Never / On failure / Always

**Step 4 — Permission Configuration**

Configure platform capabilities the application can use:

- **AI Models**: Select available inference models on the device, set max QPS
- **Video Streams**: Select accessible video streams (e.g., main stream, sub stream)
- **Event Permissions**: Set publishable and subscribable event topics (comma-separated, supports wildcards)
- **Network Mode**: Isolated (no network) or Host (shared host network)
- **Device Control**: Select required hardware control permissions (fill light, IR cut filter, PTZ)

**Step 5 - Advanced Configuration** (Optional)

- **Environment Variables**: Add key-value pairs to inject into the container environment
- **Volume Mounts**: Configure directory mapping between host and container

**Step 6 — Confirm Installation**

Review all configuration details and click the **Install** button to proceed. The application will appear in the application list after installation completes.

.. _app_image_step5:

Step 5: Command Line Import (Alternative)
------------------------------------------

If you cannot use the Web Console, first transfer the image to the device via SCP, then import it through the command line.

Transfer the image to the device:

.. code-block:: bash

   scp my-app.tar.gz root@<device-ip>:/tmp/

Then SSH into the device and use aipc-cli:

.. code-block:: bash

   # Install the application
   aipc-cli app install --manifest /tmp/app.yaml --image /tmp/my-app.tar

   # Start the application
   aipc-cli app start my_app

   # List application status
   aipc-cli app list

   # View application logs
   aipc-cli app logs my_app

You can also use a gRPC client to directly call the app-manager service:

.. code-block:: bash

   grpcurl -plaintext \
     -d '{"manifest_path": "/tmp/app.yaml", "image_path": "/tmp/my-app.tar"}' \
     unix:///run/aipc/app-manager.sock \
     appmanager.AppManager/InstallApp

.. _app_yaml_reference:

Application Manifest Reference (app.yaml)
------------------------------------------

Below is a detailed description of each field in ``app.yaml``.

Metadata
~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 20 10 70

   * - Field
     - Required
     - Description
   * - id
     - Yes
     - Unique application identifier (lowercase letters, numbers, underscores)
   * - name
     - Yes
     - Application display name
   * - version
     - Yes
     - Semantic version number (e.g., 1.0.0)
   * - description
     - Yes
     - Application description
   * - author
     - No
     - Author name
   * - email
     - No
     - Contact email

Resource Limits (spec.resources)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 15 15 70

   * - Field
     - Default
     - Description
   * - cpu
     - —
     - CPU limit, e.g., ``"50%"`` or ``"0.5"``
   * - memory
     - —
     - Memory limit, e.g., ``"256Mi"`` or ``"1Gi"``
   * - shm
     - false
     - Enable shared memory (required for zero-copy video streams)

Permission Configuration (spec.permissions)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Video Stream Permissions (video)**

Specify video streams the application can access:

- ``cam0_main.raw`` — Raw video stream (via SHM zero-copy)
- ``cam0_sub.raw`` — Sub-stream raw video
- ``cam0_main`` — Encoded video stream (via Unix socket)

**AI Inference Permissions (inference)**

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Field
     - Default
     - Description
   * - models
     - []
     - List of usable models
   * - max_qps
     - —
     - Maximum QPS limit
   * - max_concurrent
     - —
     - Maximum concurrent inferences

**Event Bus Permissions (events)**

- ``publish`` — Publishable event topics (supports wildcards ``*``)
- ``subscribe`` — Subscribable event topics (supports wildcards ``*``)

**Device Control Permissions (device)**

.. list-table::
   :header-rows: 1
   :widths: 15 15 70

   * - Field
     - Default
     - Description
   * - light
     - false
     - Fill light control
   * - ir_cut
     - false
     - IR cut filter control
   * - ptz
     - false
     - PTZ control
   * - lens
     - false
     - Lens zoom/focus control

**Network Permissions (network)**

- ``mode`` — Network mode: ``"isolated"`` (default) or ``"host"``
- ``outbound`` — Allowed outbound addresses (in isolated mode)

Lifecycle Configuration
~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Field
     - Default
     - Description
   * - autostart
     - false
     - Automatically start on system boot
   * - restart_policy
     - "no"
     - Restart policy: always / on-failure / no
   * - restart_max_retries
     - 3
     - Maximum restart attempts (on on-failure)

Health Check
~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 15 15 70

   * - Field
     - Default
     - Description
   * - enabled
     - false
     - Enable health check
   * - interval
     - 30s
     - Check interval
   * - timeout
     - 5s
     - Timeout duration
   * - retries
     - 3
     - Failure retry count

.. _app_image_faq:

FAQ
---

Image Build Failure
~~~~~~~~~~~~~~~~~~~

**Error**: ``failed to solve: failed to fetch``

Check network connectivity. If a proxy is needed:

.. code-block:: bash

   docker build --build-arg HTTP_PROXY=http://proxy:port \
                --build-arg HTTPS_PROXY=http://proxy:port \
                -t my-app:1.0.0 .

Image File Too Large
~~~~~~~~~~~~~~~~~~~~

Using gzip compression can reduce file size by approximately 70%:

.. code-block:: bash

   docker save my-app:1.0.0 | gzip > my-app.tar.gz

Import Failure
~~~~~~~~~~~~~~

**Error**: ``Failed to import image to containerd``

.. code-block:: bash

   # Check containerd status
   systemctl status containerd

   # Manual import test
   ctr -n aipc images import my-app.tar

Permission Error
~~~~~~~~~~~~~~~~

**Error**: ``Permission denied``

.. code-block:: bash

   chmod 644 /tmp/app.yaml /tmp/my-app.tar
