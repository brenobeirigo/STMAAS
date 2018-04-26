import gen.map as map

G = map.load_network("delft-the-netherlands", "C:/Users/breno/OneDrive/Phd_TU/PROJECTS/STMAASSL2018/STMAASSL/data/network")

print("Nodes:", len(G.nodes()))

print("Edges:", len(G.edges()))