# sankaku_complex_downloader
download sankaku_beta images from tag information


# description
download images from https://beta.sankakucomplex.com/

Example : https://beta.sankakucomplex.com/wiki/en?tagName=oxxo

  -> url contain tag [oxxo]
  
  -> our programs get all images from this tag


# before use
  
  Install python3 on pc
  Install librarys from pip
  
  download this project to your pc
  
  Open down_complex_APIv3.py with Text Editor
  change there information
  1. USER             : sankaku complex user ID
  2. PASSWORD         : sankaku complex user password
  3. def_save_path    : images save path on your computer
  
  
# how to use
 
    py down_complex_APIv3 [tag_name] or [txt_path]
  
  [txt_path]
      -> txt can contain multiple tags (split /n)
      
      Example: https://beta.sankakucomplex.com/wiki/en?tagName=oxxo
      
                -> oxxo
      
      -> py down_complex_APIv3 ./tag_list.txt         
       
      
  [tag_name]
  
      ->https://beta.sankakucomplex.com/wiki/en?tagName=oxxo
                -> oxxo
           
      -> py down_complex_APIv3 oxxo
