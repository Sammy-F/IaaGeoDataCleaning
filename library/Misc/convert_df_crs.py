def convert_df_crs(df, out_crs=4326):
   """Change projection from input projection to provided crs (defaults to 4326)"""
   import pyproj
   from functools import partial
   from shapely.ops import transform

   def get_formatted_crs(crs):
       """Determine correct crs string based on provided [out_crs] value"""
       try:
           new_crs = pyproj.Proj(crs)
           dcs = new_crs
           ncrs_str = crs
       except AttributeError:
           try:
               float(crs)
               new_crs = 'epsg:{}'.format(crs)
               dcs = pyproj.Proj(init=new_crs)
               ncrs_str = {'init': '{}'.format(new_crs)}
           except TypeError:
               new_crs = crs
               dcs = pyproj.Proj(init=new_crs)
               ncrs_str = {'init': new_crs}
       except RuntimeError:
           new_crs = out_crs
           dcs = pyproj.Proj(new_crs)
           ncrs_str = new_crs

       return dcs, new_crs, ncrs_str

   scs, _,_ = get_formatted_crs(df.crs)
   # get destination coordinate system, new coordinate system and new crs string
   dcs, new_crs, ncrs_str = get_formatted_crs(out_crs)
   project = partial(
       pyproj.transform,
       scs,  # source coordinate system
       dcs)  # destination coordinate system
   new_df = df[[x for x in df.columns if x != 'geometry']]
   new_geom = [transform(project, x) for x in df.geometry.values]
   new_df['geometry'] = new_geom
   new_spat_df = gp.GeoDataFrame(new_df, crs=ncrs_str, geometry='geometry')
   # return dataframe with converted geometry
return new_spat_df
