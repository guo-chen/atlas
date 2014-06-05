#!/usr/bin/python

# Written in python 2.4

# Atlas is able to: 
#     1) Generate a file (named .atlas) of mapping relationship 
#        for all the symbolic links and their destination in the 
#        specified folder recursively, and is able to create
#        a list identifying dead links.
#     2) Identify the specified folder or file if it is being
#        referred by other symbolic links according to a specified
#        .atlas file.

# 2014-05-07: Ver. 0.1: Initial version
# 2014-05-08: Ver. 0.2: Added support for identifying symbolic links
#                       to files and identifying dead links.
# 2014-05-12: Ver. 0.3: Improved function checkTarget() to make it
#                       possible to check the parent directory of 
#                       the candidate target. As a result, Atlas is
#                       able to check the situation when some folder
#                       or file is not linked by any symlinks but
#                       its parent or upper folder is linked.
# 2014-05-13: Ver. 0.4: 1) Added support for 'verbose' mode for 
#                          functions;
#                       2) Added parser for options;
#                       3) Some minor fixes.
# 2014-05-13: Ver. 1.0: First release edition
# 2014-05-14: Ver. 1.1: Added alive message when generating 
#                       relatively large atlas in case users think
#                       the tool is hang and kill it.
# 2014-05-15: Ver. 1.2: Added support for taking a list of target_paths
#                       to generate .atlas or check.
# 2014-05-16: Ver. 1.3: Added support for updating .atlas based on
#                       the target_paths given. dead_links.list will
#                       also be updated. (Optimised mergeAtlas() for
#                       performance)
# 2014-05-27: Ver. 1.4: Added support for removing the symolic links
#                       to a target path in p4, but submitting the 
#                       change is still manual due to safety reasons.

import sys, os, optparse
import time

def writeAtlas(dict, file_path='./', sep=':', verbose=False):
    if not file_path.endswith('/'):
        file_name=file_path+'/'+".atlas"
    else:
        file_name=file_path+".atlas"
    try:
        fileHandler = open(file_name, "w")
    except IOError:
        print ("Cannot open '%s' for writing."%file_name)
        sys.exit(-1)
    for key in dict.keys():
        fileHandler.write("%s%s"%(key,sep))
        for i in dict[key]:
            fileHandler.write("%s "%i)
        fileHandler.write("\n")
    fileHandler.close()
    if verbose:
        print ("'%s' written."%file_name)

def readAtlas(file_path='./', sep=':', verbose=False):
    if not file_path.endswith('/'):
        file_name=file_path+'/'+".atlas"
    else:
        file_name=file_path+".atlas"
    dict = {}
    if verbose:
        start_time=time.time()
    try:
        fileHandler = open(file_name, "r")
    except IOError:
        print ("Cannot open '%s' for reading. Please specify the path of atlas, or use -g option to generate one."%file_name)
        sys.exit(-1)
    for line in [readline.strip() for readline in fileHandler]:
        (key,value)=(line.split(sep)[0], line.split(sep)[-1].split())
        dict[key]=value
    fileHandler.close()
    if verbose:
        print("Atlas read in %.2fs."%(time.time()-start_time))
    return dict

def mergeList(list_of_lists):
    merged_list=[]
    for i in list_of_lists:
        merged_list=list(set(merged_list+i))
    merged_list.sort()
    return merged_list


def mergeAtlas(base_atlas, atlas_list, verbose = False):
    if verbose:
        print("Merging atlas...")
        start_time = time.time()
    merged_atlas=base_atlas
    dict_list = atlas_list[:]
    for dict in dict_list:
        for key in dict.keys():
            if key not in merged_atlas.keys():
                merged_atlas[key]=dict[key]
            else:
                merged_atlas[key]=list(set(merged_atlas[key]+dict[key]))
    if verbose:
        print("Atlas merged in %.2fs."%(time.time()-start_time))
    return merged_atlas

def writeList2File(list, file_name = "dead_links.list", file_path = "./", verbose=False):
    try:
        fileHandler = open(file_path+file_name, "w")
    except IOError:
        print ("Cannot write %s"%(file_path+file_name))
        sys.exit(-1) 
    for i in list:
        fileHandler.write("%s\n"%i)
    fileHandler.close()
    if verbose:
        print("File '%s' written."%file_name)
    

def readFile2List(file_name= "dead_links.list", file_path = './', verbose=False):
    try:
        list = [line.strip() for line in open(file_path+file_name)]
    except IOError:
        print ("Cannot open %s"%(file_path+file_name))
        sys.exit(-1)
    return list


def generateAtlas(check_path_list, verbose = False):
    # returen a tuple (atlas, deadlink)
    to_check_list = [os.path.realpath(i) for i in check_path_list]

    atlas_list = []
    dead_link_list = []

    for to_check in to_check_list:
        if os.path.exists(to_check):
            start_time=time.time()
            atlas = {}
            dead_links = []
            print("Generating atlas for path '%s'..."%to_check)
            loop_start_time = time.time() # time stamp for tracking time spent to print out alive message.
            for root, dirs, files in os.walk(to_check, topdown=True):
                # Handling links to directories
                for name in dirs:
                    dir_abs_path = os.path.join(os.path.abspath(root),name)
                    if os.path.islink(dir_abs_path):
                        target=os.path.realpath(dir_abs_path)
                        if target not in atlas.keys():
                            atlas[target]=[dir_abs_path]
                        else:
                            atlas[target].append(dir_abs_path)
               # Handling links to files
                for name in files:
                    file_abs_path = os.path.join(os.path.abspath(root),name)
                    if os.path.islink(file_abs_path):
                        target=os.path.realpath(file_abs_path)
                        # deadlinks are treated as files, they should be handled
                        if os.path.exists(target):
                            if target not in atlas.keys():
                                atlas[target]=[file_abs_path]
                            else:
                                atlas[target].append(file_abs_path)
                        else:
                            dead_links.append(file_abs_path)
                if time.time()-loop_start_time > 300: # 5 mins later...
                    print("Well, this could take a while, I am still alive, please don't kill me ...")
                    loop_start_time=time.time()
            if verbose:
                print("Atlas generation took %.2fs."%(time.time()-start_time))
            #return (atlas, dead_links)
            if atlas:
                atlas_list.append(atlas)
                if verbose:
                    print("\tatlas for '%s' created"%to_check)
            if dead_links:
                dead_link_list.append(dead_links)
        else:
            print("'%s' does not exist, ignored"%to_check)
            #return (None, None)
            pass

    if atlas_list:
        merged_atlas = mergeAtlas(base_atlas={},atlas_list=atlas_list, verbose=verbose)
    else:
        merged_atlas = {}
    if dead_link_list:
        merged_dead_link = mergeList(dead_link_list)
    else:
        merged_dead_link = []
    return (merged_atlas, merged_dead_link)

    

def updateAtlas(check_path_list, atlas_path = "./", verbose = False):
    #to_check_list = [os.path.realpath(i) for i in check_path_list]
    if not atlas_path.endswith('/'):
        atlas_path=atlas_path+'/'
    atlas=readAtlas(file_path=atlas_path, verbose=verbose) 
    dead_links = readFile2List(file_path=atlas_path, verbose=verbose)
    (atlas_to_update, dead_links_to_update) = generateAtlas(check_path_list=check_path_list[:], verbose=verbose)
    print("Updating atlas ...")
    updated_atlas = mergeAtlas(base_atlas=atlas, atlas_list=[atlas_to_update],verbose=verbose)
    print("Updating dead_links ...")
    updated_deadlinks = mergeList([dead_links, dead_links_to_update])
    return (updated_atlas, updated_deadlinks) 
	
def checkTarget(dict, target_name_list):
    symlink_list=[]
    if dict:
        for target_name in target_name_list:
            to_check = os.path.realpath(target_name)
            if os.path.exists(to_check):
                flag_linked = False
                print("If you modify '%s', the following will be affected:"%target_name)
                while(to_check !='/'):
                    if to_check in dict.keys():
                        print("\t%s\t[target]"%to_check) # print the real target if 'target_name' is a link or it is itself if 'target_name' is a real directory
                        for i in dict[to_check]:
                            print("\t%s"%i)
                            symlink_list.append(i)
                        flag_linked = True
                        #break Should not stop, need to continue to see if all the parents are not linked.
                    to_check = os.path.dirname(to_check) 
                if not flag_linked:
                    print("Nothing linked to '%s', you are free to go."%target_name)
            else:
                print("'%s' does not exist, or it is a dead symbolic link"%target_name)
        return symlink_list
    else:        
        print("Input Dictionary is empty, unable to check '%s'."%target_name)
        return symlink_list
		
def main():
    
    # Create parser for options
    usage = "Usage: %prog [options] target_path1 target_path2 ..."
    description = "Atlas is used to check if a target is linked by any other symbolic \
                   links according to an .atlas file (a map indicating the mapping \
                   relationship of all symbolic links in an interested directory and \
                    their targets), which could be generated or updated by Atlas too."
    parser=optparse.OptionParser(usage=usage, description=description)
    parser.add_option("-v", '--verbose', action='store_true', dest='verbose', default=False, help="show more detailed information")
    parser.add_option("-g", '--generate', action='store_true', dest='generate', default=False, help="make Atlas to work in 'generate' mode, target_path is used as interested directory to create atlas file in this mode, cannot be used together with -u (--update)")
    parser.add_option("-u", '--update', action='store_true', dest='update', default=False, help="update .atlas file based on the target_path, cannot be used together with -g (--generate)")
    parser.add_option("-d", '--delete', action='store_true', dest='delete', default=False, help="delete links to target_path in Perforce, cannot be used together with -g and -u")
    parser.add_option('-p', '--atlas-path', action='store', dest='atlas_path', default='/tmp/', metavar='PATH', help="specify where to read .atlas or write .atlas (when -g is specified), the default value is the temparory path ('/tmp/')")
    opts, args = parser.parse_args()
   
    if (opts.generate and opts.update) or (opts.generate and opts.delete) or (opts.update and opts.delete):
        parser.print_help()
        parser.error("options -g, -u and -d cannot be used together") 
    elif not args:
        parser.print_help()
        parser.error("at least one target_path must be specified")
    else:
        target_path_list=args[:]
        if opts.generate == True:
            # Working in generate mode
            if not opts.atlas_path.endswith('/'):
                opts.atlas_path=opts.atlas_path+'/'
            (atlas, dead_links)=generateAtlas(check_path_list=target_path_list, verbose=opts.verbose)
            if atlas:
                writeAtlas(dict=atlas, file_path=opts.atlas_path, verbose=opts.verbose)
            if dead_links:
                writeList2File(list=dead_links, file_path=opts.atlas_path, verbose=opts.verbose) 
                print ("Dead links found, written in '%sdead_links.list'"%opts.atlas_path)
        elif opts.update == True:
            if not opts.atlas_path.endswith('/'):
                opts.atlas_path=opts.atlas_path+'/'
            (atlas, dead_links)=updateAtlas(check_path_list=target_path_list, atlas_path=opts.atlas_path, verbose=opts.verbose)
            if atlas:
                writeAtlas(dict=atlas, file_path=opts.atlas_path, verbose=opts.verbose)
            if dead_links:
                writeList2File(list=dead_links, file_path=opts.atlas_path, verbose=opts.verbose) 
            print("Update complete.")
        elif opts.delete == True:
            print("Warning: Working in delete mode")
            atlas = readAtlas(file_path=opts.atlas_path, verbose=opts.verbose)
            symlink_list=checkTarget(dict = atlas, target_name_list = target_path_list)
            if symlink_list:
                for symlink in symlink_list:
                    os.chdir(os.path.dirname(symlink))
                    os.system("p4 delete "+symlink.split('/')[-1])

        else:
            # Working in check mode
            atlas = readAtlas(file_path=opts.atlas_path, verbose=opts.verbose)
            symlink_list=checkTarget(dict = atlas, target_name_list=target_path_list)
    
if __name__ == "__main__":
	main()
