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
    server_players_qty = [len(ele.find_all('span', {'class':'visname'}, text=True)) for ele in soup.findAll('div', {'class': 'server-players'})]
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
