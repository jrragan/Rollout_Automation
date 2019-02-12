import logging

from ciscoconfparse import CiscoConfParse
from jsonpath_ng import jsonpath, parse
from objectpath import Tree

logger = logging.getLogger('helpers')

def update_config(template, parse):
    logger.info("update_config function")
    #parse template
    logger.debug("update_config: template: {}".format(template))
    tparse1 = CiscoConfParse(template.splitlines())
    logger.debug("update_config: tparse1: {}".format(tparse1))

    #get all objects
    objs1 = tparse1.find_objects('.*')
    logger.debug(objs1)

    #check for parents
    par1 = tparse1.find_parents_w_child('.*', '.*')
    logger.debug("update_config: parents in template: {}".format(par1))

    for obj in objs1:
        logger.debug("update_config: obj: {}".format(obj))
        logger.debug("is_parent: {}".format(obj.is_parent))
        logger.debug("is_child: {}".format(obj.is_child))
        if not obj.is_parent and not obj.is_child:
            logger.debug("obj {} is not parent or child".format(obj))
            if not parse.find_objects(r"^{}\s*$".format(obj.text)):
                parse.append_line(obj.text)
    parse.commit()

    if par1:
        for parent in par1:
            logger.debug("== parent {} ==".format(parent))
            children = tparse1.find_children_w_parents(r"^{}\s*$".format(parent), r'.*')
            logger.debug("children: {}".format(children))
            cobj = parse.find_objects(r"^{}\s*$".format(parent))
            logger.debug(cobj)
            if cobj:
                cobj = cobj[0]
                logger.debug("== cobj {} ==".format(cobj))
                if cobj.is_parent:
                    logger.debug("update_config: cobj.is_parent")
                    children.reverse()
                    for child in children:
                        logger.debug("update_config: parent: child: {}".format(child))
                        if not cobj.has_child_with(r"{}\s*$".format(child)):
                            logger.debug("update_config: cobj not have child: {}, writing line".format(child))
                            cobj.append_to_family(child)
                else:
                    logger.debug("update_config: cobj is not parent")
                    parse.insert_after(cobj.text, children[0])
                    parse.commit()
                    previous = children[0]
                    for child in children[1:]:
                        logger.debug("update_config: not parent: child: {}".format(child))
                        parse.insert_after(regex_modify(previous), child)
                        previous = child
                        parse.commit()
            else:
                logger.debug("== not cobj ==")
                parse.append_line(parent)
                parse.commit()
                previous = parent
                for child in children:
                    logger.debug("update_config: not cobj: child: {}".format(child))
                    #logger.debug(parse.find_objects(previous))
                    logger.debug("update_config: not cobj: previous: {}".format(previous))
                    logger.debug(parse.find_objects(regex_modify(previous)))
                    parse.insert_after(regex_modify(previous), child)
                    previous = child
                    parse.commit()
    parse.commit()
    return parse

def regex_modify(text):
    meta = r"+{}[]|()?"
    for c in meta:
        if c in text:
            text = r"{}".format(text.replace(c, r"\{}".format(c)))
    return text

def json_xpath(param, json_path):
    if isinstance(json_path, str):
        json_path = [json_path]
    results = []
    tree = Tree(param)
    for path in json_path:
        jsonpath_expr = tree.execute(path)
        if jsonpath_expr:
            results.extend(jsonpath_expr)
    return results


