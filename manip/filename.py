
def get_file_name(region):
    return region.lower().replace(" ", "-").replace(",", "")
    

# Network instance file name
def get_instance_file_name(nw_type,i,graph,p,n_zones=0):
    # File name
    file_name = ""
    if n_zones == 0:
        file_name = "{0}_{1}_S{2:03}_SUB_{3:02}".format(graph,
                            nw_type,
                            int(100*p),
                            i)
    else:
        file_name = "{0}_{1}_S{2:03}_Z{3:02}_{4:02}".format(graph,
                            nw_type,
                            int(100*p),
                            n_zones,
                            i)
    return file_name