import logging
from copy import deepcopy

from jinja2 import Template

from rules.rule import Rule

logger = logging.getLogger(__name__)


class TemplateRule(Rule):
    def set_config_template(self, template=None, modify_variables=None):
        """

        :param template: a jinja2 template string
        :param modify_variables: optional function to modify variables before passing them to the template engine
        :return:
        """
        self._template = template
        self._modify_variables_func = modify_variables

    @property
    def template(self):
        return self._template

    def generate_config(self, objects):
        logger.debug("generate_config: received objects: {}".format(objects))
        t = Template(self.template)
        local_objects = deepcopy(objects)
        if self._modify_variables_func is not None:
            local_objects = self._modify_variables_func(local_objects)
        logger.debug("generate_config: rule: {}, objects: {}".format(self.exception, local_objects))
        config = t.render(objects=local_objects)
        logger.debug("generate_config: rule: {}, config: {}".format(self.exception, config))
        return config
