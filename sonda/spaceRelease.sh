Watched_Directory=$1
echo "Directory to limit="$Watched_Directory

Max_Directory_Percentage=$2
echo "Percentage of partition this directory is allowed to use="$Max_Directory_Percentage

Directory_Size=$( du -sk "$Watched_Directory" | cut -f1 )
echo "Current size of this directory="$Directory_Size

Disk_Size=$(( $(df $Watched_Directory | tail -n 1 | awk '{print $3}')+$(df $Watched_Directory | tail -n 1 | awk '{print $4}') ))       
echo "Total space of the partition="$Disk_Size

Directory_Percentage=$(echo "scale=2;100*$Directory_Size/$Disk_Size+0.5" | bc | awk '{printf("%d\n",$1 + 0.5)}')
echo "Curent percentage used by the directory="$Directory_Percentage

Number_Files_Deleted_Each_Loop=$3
echo "number of files to be deleted every time the script loops="$Number_Files_Deleted_Each_Loop

while [ $Directory_Percentage -gt $Max_Directory_Percentage ] ; do
    find $Watched_Directory -type f -printf "%T@ %p\n" | sort -nr | tail -$Number_Files_Deleted_Each_Loop | cut -d' ' -f 2- | xargs rm
    find $Watched_Directory -type d -empty -delete
    Directory_Size=$( du -sk "$Watched_Directory" | cut -f1 )
    Directory_Percentage=$(echo "scale=2;100*$Directory_Size/$Disk_Size+0.5" | bc | awk '{printf("%d\n",$1 + 0.5)}')
done