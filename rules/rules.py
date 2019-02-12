from rules.condition.block_match import BlockMatch
from rules.condition.child_match import ChildMatch
from rules.condition.match import Match
from rules.rule import Rule

default_vdc_rules = {}
fpath_vdc_rules = {}
def build_rules():
    nxos_interface_fpath_match = Match("nxos_interface_fpath", r"^interface",
                                       [(True, r"switchport\s+mode\s+fabricpath"), (False, r"vpc\s+peer-link"),
                                        (True, r"^\s*no\s+shutdown"), (False, r"channel\-group\s+\d+")])
    nxos_interface_fpath_rule = Rule("Shutdown fabricpath ports")
    nxos_interface_fpath_rule.set_confirm_match(nxos_interface_fpath_match)
    template = "{% for interface in objects['nxos_interface_fpath'][0] %}\n{{ interface.text }}\n  shutdown\n{% endfor %}\n" \
               "\n********** Undo **********\n" \
               "{% for interface in objects['nxos_interface_fpath'][0] %}\n{{ interface.text }}\n  no shut\n{% endfor %}\n"
    nxos_interface_fpath_rule.set_config_template(template)
    fpath_vdc_rules["fpath"] = nxos_interface_fpath_rule

    nxos_interface_vpc_match = Match("nxos_interface_vpc", r"interface port-channel",
                                        [(True, r"vpc\s+\d+"), (False, r"^\s*shutdown")])
    nxos_interface_vpc_rule = Rule("Shutdown vpc ports")
    nxos_interface_vpc_rule.set_confirm_match(nxos_interface_vpc_match)
    template = "{% for interface in objects['nxos_interface_vpc'][0] %}\n{{ interface.text }}\n  shutdown\n{% endfor %}\n" \
               "\n********** Undo **********\n" \
               "{% for interface in objects['nxos_interface_vpc'][0] %}\n{{ interface.text }}\n  no shut\n{% endfor %}\n"
    nxos_interface_vpc_rule.set_config_template(template)
    default_vdc_rules[545325] = nxos_interface_vpc_rule
    fpath_vdc_rules[545325] = nxos_interface_vpc_rule

    nxos_interface_pka_match = Match("nxos_interface_pka", r"^interface",
                                       [(True, r"^\s*ip\s+address"), (True, r"vrf\s+member\s+vpc\-keepalive"),
                                        (False, r"^\s*shutdown")])
    nxos_interface_pka_rule = Rule("Shutdown PKA")
    nxos_interface_pka_rule.set_confirm_match(nxos_interface_pka_match)
    template = "{% for interface in objects['nxos_interface_pka'][0] %}\n{{ interface.text }}\n  shutdown\n{% endfor %}\n" \
               "\n********** Undo **********\n" \
               "{% for interface in objects['nxos_interface_pka'][0] %}\n{{ interface.text }}\n  no shut\n{% endfor %}\n"
    nxos_interface_pka_rule.set_config_template(template)
    default_vdc_rules["pka"] = nxos_interface_pka_rule
    fpath_vdc_rules["pka"] = nxos_interface_pka_rule

    nxos_interface_peerlink_match = Match("nxos_interface_peerlink", r"interface port-channel",
                                     [(True, r"vpc\s+peer-link"), (False, r"^\s*shutdown")])
    nxos_interface_peerlink_rule = Rule("Shutdown vpc peer link ports")
    nxos_interface_peerlink_rule.set_confirm_match(nxos_interface_peerlink_match)
    template = "{% for interface in objects['nxos_interface_peerlink'][0] %}\n{{ interface.text }}\n  shutdown\n{% endfor %}\n" \
               "\n********** Undo **********\n" \
               "{% for interface in objects['nxos_interface_peerlink'][0] %}\n{{ interface.text }}\n  no shut\n{% endfor %}\n"
    nxos_interface_peerlink_rule.set_config_template(template)
    default_vdc_rules["peerlink"] = nxos_interface_peerlink_rule
    fpath_vdc_rules["peerlnk"] = nxos_interface_peerlink_rule

    bgp_router_match = Match("bgp_router", "global", "^router\s+bgp")
    # bgp_routemap_match = BlockMatch("bgp_routemap_match", r"^\s+route-map")
    # bgp_neighbors_af_match = ChildMatch("bgp_neighbors_af_match", r"\s+neighbor", r"\s+(address-family.*)")
    # bgp_routemap_rule = Rule("BGP Prepend to All Neighbors")
    # bgp_routemap_rule.set_confirm_match(bgp_router_match, '&', bgp_routemap_match, '&', bgp_neighbors_af_match)
    # """
    # !*** BGP Prepend to All Neighbors ***
    #  {'bgp_router': [[<IOSCfgLine # 225 'router bgp 65534'>]],
    #  'bgp_routemap_match': ['router bgp 65534', '  neighbor 172.29.231.238 remote-as 65534', '    address-family ipv4 unicast',
    #  '      route-map CIENA-ROUTES out', '  neighbor 172.29.231.246 remote-as 65534', '    address-family ipv4 unicast',
    #  '      route-map CIENA-ROUTES out', '  neighbor 172.29.231.250 remote-as 65534', '    address-family ipv4 unicast',
    #  '      route-map CIENA-ROUTES ou'],
    #  'bgp_neighbors_af_match': {'parents': [<IOSCfgLine # 228 '  neighbor 172.26.33.194 remote-as 65535' (parent is # 225)>,
    #  <IOSCfgLine # 231 '  neighbor 172.29.231.238 remote-as 65534' (parent is # 225)>,
    #  <IOSCfgLine # 235 '  neighbor 172.29.231.246 remote-as 65534' (parent is # 225)>,
    #  <IOSCfgLine # 239 '  neighbor 172.29.231.250 remote-as 65534' (parent is # 225)>],
    #  'children': {'  neighbor 172.26.33.194 remote-as 65535': ('address-family ipv4 unicast',),
    #  '  neighbor 172.29.231.238 remote-as 65534': ('address-family ipv4 unicast',),
    #  '  neighbor 172.29.231.246 remote-as 65534': ('address-family ipv4 unicast',),
    #  '  neighbor 172.29.231.250 remote-as 65534': ('address-family ipv4 unicast',)}}}
    # """
    # template = "route-map THESOUTHERNREACH permit 10\n  set as-path prepend 65534 65534 65534 65534 \n" \
    #            "{{ objects['bgp_router'][0][0].text }}" \
    #            "{% for neighbor, af_tuple in objects['bgp_neighbors_af_match']['children'].items() %}\n" \
    #            "{{ neighbor }}\n" \
    #            "{% for af in af_tuple %}" \
    #            "    {{ af }}\n" \
    #            "      route-map THESOUTHERNREACH out\n" \
    #            "{% endfor %}\n" \
    #            "{% endfor %}\n" \
    #            "\n ********** Undo **********\n" \
    #            "{{ objects['bgp_router'][0][0].text }}" \
    #            "{% for neighbor, af_tuple in objects['bgp_neighbors_af_match']['children'].items() %}\n" \
    #            "{{ neighbor }}\n" \
    #            "{% for af in af_tuple %}" \
    #            "    {{ af }}\n" \
    #            "      no route-map THESOUTHERNREACH out\n" \
    #            "{% endfor %}\n" \
    #            "{% endfor %}\n" \
    #            "{% for line in objects['bgp_routemap_match'] %}" \
    #            "{{ line  }}\n" \
    #            "{% endfor %}\n"
    # bgp_routemap_rule.set_config_template(template)
    bgp_shutdown_rule = Rule("Shutdown BGP routing")
    bgp_shutdown_rule.set_confirm_match(bgp_router_match)
    template = "{{ objects['bgp_router'][0][0].text }}" \
               " shutdown\n" \
               "\n ********** Undo **********\n" \
               "{{ objects['bgp_router'][0][0].text }}" \
               "  no shutdown\n"
    bgp_shutdown_rule.set_config_template(template)
    default_vdc_rules["bgp"] = bgp_shutdown_rule

    ospf_router_match = Match("ospf_router", "global", "^router\s+ospf")
    ospf_shutdown_match = Match("ospf_max_lsa", r"^\s*router ospf", (False, r"max-metric router-lsa"))
    ospf_shutdown_rule = Rule("Disable OSPF routing")
    ospf_shutdown_rule.set_confirm_match(ospf_router_match, '&', ospf_shutdown_match)
    template = "{% for router in objects['ospf_router'][0] %}\n{{ router.text }}\n  max-metric router-lsa\n{% endfor %}\n" \
               "\n ********** Undo **********\n" \
               "{% for router in objects['ospf_router'][0] %}\n{{ router.text }}\n  no max-metric router-lsa\n{% endfor %}\n"
    ospf_shutdown_rule.set_config_template(template)
    default_vdc_rules["ospf shutdown"] = ospf_shutdown_rule

    nxos_interface_ipint_match = Match("nxos_interface_ipint", r"^interface\s+(?:Ethernet)",
                                       [(True, r"^\s*ip\s+address"),
                                        (False, r"vrf\s+member\s+vpc\-keepalive"),
                                        (True, r"^\s*no\s+shutdown")])
    nxos_interface_ipint_rule = Rule("Shutdown L3 Interfaces")
    nxos_interface_ipint_rule.set_confirm_match(nxos_interface_ipint_match)
    template = "{% for interface in objects['nxos_interface_ipint'][0] %}\n{{ interface.text }}\n  shutdown\n{% endfor %}\n" \
               "\n ********** Undo **********\n" \
               "{% for interface in objects['nxos_interface_ipint'][0] %}\n{{ interface.text }}\n  no shut\n{% endfor %}\n"
    nxos_interface_ipint_rule.set_config_template(template)
    default_vdc_rules["ipint"] = nxos_interface_ipint_rule

    nxos_pc_ipint_match = Match("nxos_pc_ipint", r"^interface\s+(?:port\-channel)",
                                       [(True, r"^\s*ip\s+address"),
                                        (False, r"vrf\s+member\s+vpc\-keepalive"),
                                        (False, r"^\s*shutdown")])
    nxos_pc_ipint_rule = Rule("Shutdown L3 PC Interfaces")
    nxos_pc_ipint_rule.set_confirm_match(nxos_pc_ipint_match)
    template = "{% for interface in objects['nxos_pc_ipint'][0] %}\n{{ interface.text }}\n  shutdown\n{% endfor %}\n" \
               "\n ********** Undo **********\n" \
               "{% for interface in objects['nxos_pc_ipint'][0] %}\n{{ interface.text }}\n  no shut\n{% endfor %}\n"
    nxos_pc_ipint_rule.set_config_template(template)
    default_vdc_rules["pcipint"] = nxos_pc_ipint_rule

