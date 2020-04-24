import h5pyd as h5py

print("version:", h5py.version.version)

f = h5py.File("/terra/TERRA_BF_L1B_O9820_20011022161559_F000_V001.h5", "r",
              username='admin', password='admin',
              endpoint="http://ec2-3-135-220-122.us-east-2.compute.amazonaws.com")

# print("filename,", f.filename)
print("name:", f.name)
print("id:", f.id.id)
print(list(f.keys()))
