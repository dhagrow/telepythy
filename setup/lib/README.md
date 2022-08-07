# Telepythy Service

This is the service library for [Telepythy][1]. This library has no dependencies, is supported on Python 2.7+ and 3.3+, and can be used to embed a **Telepythy** client or server into any environment.

To install, simply use:

```shell
$pip install telepythy-service
```

You can start the service directly on the command-line:

```shell
$ telepythy
# or
$ python -m telepythy
```

This will start a server listening on the default interface: `localhost:7373`. See the command-line options for other ways to run the service.

To embed a **Telepythy** service in your code, you can use any of the following functions:

```python
import telepythy

# start a server thread
telepythy.start_server()

# or start a client thread
telepythy.start_client()

# or start a client/server directly (blocking), with optional arguments
telepythy.client(locals={'client': True}, address='localhost:7373')
telepythy.server(locals={'client': False}, address='localhost:1337')
```

See the `<telepythy>/examples` directory from the [Telepythy][1] repository for examples on how to embed the service into existing code.

[1]: https://github.com/dhagrow/telepythy
