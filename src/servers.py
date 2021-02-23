import requests
from bs4 import BeautifulSoup


def scrape_servers_data():
    """ Obtains data from q3df.org/servers using web scraping"""
    url = f'https://q3df.org/serverlist'
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    server_ids = [ele.get('id').split('_')[-1] for ele in soup.findAll('div', {'class': 'server-item shadow'})]
    server_names = [ele.text for ele in soup.findAll('div', {'class': 'server-head'})]
    server_states = [ele.find('ul').text.strip('\n').split('\n') for ele in soup.findAll('div', {'class': 'server-map-info'})]
    server_players_qty = [len(ele.find_all('span', {'class':'visname'})) for ele in soup.findAll('div', {'class': 'server-players'})]
    servers_data = {}
    for i in range(len(server_ids)):
        if server_players_qty[i] > 0:
            state = server_states[i]
            server_state = {
                "ip": state[0],
                "map_name": state[1],
                "physics": state[2]
            }
            server_details = {
                "name": server_names[i],
                "state": server_state,
                "players_qty": server_players_qty[i]
            }
            servers_data[server_ids[i]] = server_details

    return servers_data


def check_if_valid_ip(ip: str):
    """
    Checks whether or not a given IP is listed on q3df.org/servers
    :param ip: The IP to validate
    :return: True or False
    """
    servers_data = scrape_servers_data()

    return len([server for (id, server) in servers_data.items() if ip == server["state"]["ip"]]) > 0


def get_most_popular_server(ignore_ip=None):
    """ Returns the IP of the server with the most players, or defrag.rocks if no servers are populated """
    servers_data = scrape_servers_data()
    if ignore_ip is not None:
        ignore_ip = ignore_ip.replace('defrag.rocks', '140.82.4.154').replace('q3df.ru', '83.243.73.220')
        if ':' not in ignore_ip:
            ignore_ip += ':27960'

    max_plyr_qty = 0
    max_plyr_ip = ""

    for id, server in servers_data.items():
        if server["players_qty"] > max_plyr_qty and server['state']['ip'] != ignore_ip:
            max_plyr_qty = server["players_qty"]
            max_plyr_ip = server["state"]["ip"]

    return max_plyr_ip


def get_next_active_server(ignore_list):
    from config import get_list
    server_data = scrape_servers_data()

    filtered_server_data = dict()
    for sv_key, sv_data in server_data.items():
        if server_data[sv_key]['state']['ip'].split(':')[0] not in get_list('whitelist_servers'):
            filtered_server_data[sv_key][sv_data] = sv_data

    server_data = filtered_server_data
    for ignore_ip in ignore_list:
        ignore_ip = ignore_ip.replace('defrag.rocks', '140.82.4.154').replace('q3df.ru', '83.243.73.220')
        if ':' not in ignore_ip:
            ignore_ip += ':27960'

    max_plyr_qty = 0
    max_plyr_ip = ""

    for id, server in server_data.items():
        if server["players_qty"] > max_plyr_qty and server['state']['ip'] not in ignore_list:
            max_plyr_qty = server["players_qty"]
            max_plyr_ip = server["state"]["ip"]

    return max_plyr_ip