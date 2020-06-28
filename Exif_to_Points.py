import os
import piexif
import csv
try:
    import arcpy 
    arc = True
except:
    print("Unable to import arcpy, point feature class won't be written")
    arc = False
        
        
search_path = r"PATH\TO\SEARCH\ALL\FOLDERS\IN"
output_path = r"PATH\TO\WRITE\OUTPUTS"


fields = ['path','DDLat','DDLon','Alt','exif_read'] #fields to write, exif_read will either be OK or ERROR if unable to read exif information
image_extensions = [".jpg",".jpeg",".raw"] #searched image formats


#converting from tuple returned by piexif to decimal degrees lat/lon
def exif_to_decimal_degrees(gps_tuple):
    
    degrees = gps_tuple[0]
    minutes = gps_tuple[1]
    seconds = gps_tuple[2]

    degrees = degrees[0]/degrees[1]
    minutes = minutes[0]/minutes[1]
    seconds = seconds[0]/seconds[1]

    return degrees + minutes/60 + seconds/3600

def valid_lon(lon):
    if lon >= -180 and lon <= 180: return True
    else: return False

def valid_lat(lon):
    if lon >= -90 and lon <= 90: return True
    else: return False
    
def valid_alt(alt):
    MARIANA_TRENCH = -11034
    HIGH_EARTH_ORBIT = 35786000
    if alt >= MARIANA_TRENCH and alt <= HIGH_EARTH_ORBIT: return True
    else: return False
    
#Takes a top level directory name and a csv output path to write to
def exif_to_csv(dir_path, output_path):

    #If the output path is a csv then details will be appended to it
    if os.path.splitext(output_path)[1].lower() == '.csv':
        pass
    #If the output path is a directory then a new csv will be created 
    elif os.path.isdir(output_path):
        output_path = os.path.join(output_path, "ExifDetails.csv")
        
        #Write headers to the csv
        with open(output_path,'a',newline='') as outfile:
            outwriter = csv.writer(outfile)
            outwriter.writerow(fields)
    else:
        print("Please provide a directory or a csv as the output path")
        exit()
   
    images_written = 0 
    img_lst = []
    
    #Search of directory and all sub-directories for image files
    os.chdir(dir_path)
    for root, dirs, files in os.walk(".", topdown = False):
        for name in files:
            filepath = os.path.join(os.path.join(dir_path,root[2:]), name)

            #Check if each file is in the list of image file extensions
            if os.path.splitext(filepath)[1].lower() in image_extensions:
            
                
                #Write path to dict of image details
                img_dict = {'path':filepath}
                
                #Try to read the exif details of the file
                read_failed = False
                try:
                    exif_dict = piexif.load(filepath)
                except:
                    #Unable to read exif - image file may be corrupted
                    img_dict = {'exif_read':"ERROR"}
                    read_failed = True
           
                #If able to read exif details then continue
                if not read_failed:
                
                    #Get any GPS exif information
                    for tag in exif_dict["GPS"]:
                        img_dict[piexif.TAGS["GPS"][tag]["name"]] = exif_dict["GPS"][tag]
                    
                    #Read, convert and stor latitude
                    if 'GPSLatitudeRef' in img_dict and 'GPSLatitude' in img_dict:
                        lat = exif_to_decimal_degrees(img_dict['GPSLatitude'])
                        if 'S'.encode('ASCII') == img_dict['GPSLatitudeRef']:
                            lat = -lat
                        if not valid_lat(lat): lat = None
                        img_dict['DDLat'] = lat
                    else:
                        img_dict['DDLat'] = None
                   
                    #Read, convert and stor longitude
                    if 'GPSLongitudeRef' in img_dict and 'GPSLongitude' in img_dict:
                        lon = exif_to_decimal_degrees(img_dict['GPSLongitude'])
                        if 'W'.encode('ASCII') == img_dict['GPSLongitudeRef']:
                            lon = -lon
                        if not valid_lon(lon): lon = None
                        img_dict['DDLon'] = lon
                    else:
                        img_dict['DDLon'] = None
                        
                    #Read, convert and stor altitude
                    if 'GPSAltitudeRef' in img_dict and 'GPSAltitude' in img_dict:
                        alt = img_dict['GPSAltitude'][0]/img_dict['GPSAltitude'][1]
                        if img_dict['GPSAltitudeRef'] == 1:
                            alt = -alt
                        img_dict['Alt'] = alt
                    else:
                        img_dict['Alt'] = None
                        
                    img_dict['exif_read'] = 'OK'
                    
                #Add the image to the running list of images to write output for    
                img_lst.append(img_dict)
                
                #Write block of 100 image details to the output CSV
                if len(img_lst) >= 100:
                    
                    with open(output_path,'a',newline='') as outfile:
                        outwriter = csv.writer(outfile)

                        for img in img_lst:
                            row = [img[f] for f in fields if f in img.keys()]
                            outwriter.writerow(row)
                            images_written+=1
                            
                    img_lst = []
                    print(str(images_written)+" images written to output")
    
    
    #Write any remaining images to the output csv
    with open(output_path,'a',newline='') as outfile:
        outwriter = csv.writer(outfile)

        for img in img_lst:
            row = [img[f] for f in fields if f in img.keys()]
            outwriter.writerow(row)
            images_written+=1
            
    print(str(images_written)+" images written to output")
                    
    return output_path         
 
#takes a csv with the expected fields and writes to feature class in gdb
def csv_to_featureclass(csv, output_path):

    arcpy.env.overwriteOutput = True
    
    #Check the provided path and make a gdb if necessary
    isdir = os.path.isdir(output_path)
    
    desc = arcpy.Describe(output_path)
    isgdb = desc.dataType == "Workspace"
        
    if not isdir and not isgdb:
        print("invalid output path, directory or esri geodatabase required")
        exit()
    elif isgdb:
        gdb = output_path
    elif isdir:
        arcpy.CreateFileGDB_management(output_path, "Exif_to_Points.gdb")
        gdb = os.path.join(output_path,"Exif_to_Points.gdb")
        
    #Convert csv to points feature class
    arcpy.env.workspace = gdb
    points = arcpy.management.XYTableToPoint(csv, "ExifPoints","DDLon", "DDLat", "Alt")
    
    #Change the path in the attribute table to a hyperlink
    with arcpy.da.UpdateCursor(points, ["path"]) as cursor:

        for row in cursor:
            
            path = row[0]
            row[0] = '<a href="'+ path + '" target="_top">'+path+'</a>'
            
            cursor.updateRow(row)
            
    print("Points feature class written to " + output_path)


def main():
    #Write all lat/lon/altitude to csv
    csv = exif_to_csv(search_path, output_path)
    
    #Write all lat/lon/altitude to feature class
    if arc: csv_to_featureclass(csv, output_path)
        
if __name__ == "__main__":
    main()
    

    
    
























