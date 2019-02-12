class Configuration:
    def __init__(self, filename=None, config=None, deploy='merge'):
        if filename and config:
            raise AttributeError("Both filename and config attributes can be set")
        deploy = deploy.lower()
        if deploy != 'merge' and deploy != 'replace':
            raise AttributeError("deploy must be set to either 'merge' or 'replace'")

        self._filename = filename
        self._config = config
        self._deploy = deploy

    @property
    def filename(self):
        return self._filename

    @property
    def config(self):
        return self._config

    @property
    def deploy(self):
        return self._deploy
