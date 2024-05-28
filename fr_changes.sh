#!/usr/bin/sh

set -eu

fr_base_dir="/etc/freeradius/3.0"
fr_virt_server_file="$fr_base_dir/sites-available/raa"

add_line_to_file() {
	line_to_add=$1
	file=$2
	if ! grep -qF -- "$line_to_add" "$file"; then
		awk -v line="$line_to_add" 'BEGIN {print line} {print $0}' "$file" >temp && mv temp "$file"
		echo "Line \"$line_to_add\" added to $file"
	else
		echo "Line \"$line_to_add\" already exists in $file"
	fi
}

echo "Removing default virtual server"
rm -f "$fr_base_dir/sites-enabled/default"

echo "Creating RADIUS Accounting Assurance FreeRADIUS virtual server"
cat <<_EOF_ | tee "$fr_virt_server_file"
server raa {
  listen {
    type = auth
    port = 1812
    ipaddr = *
  }
  listen {
    type = acct
    port = 1813
    ipaddr = *
  }
  authorize {
    eap {
      ok = return
    }
  }
  authenticate {
    eap
  }
  accounting {
    ok
  }
  post-auth {
    if &reply:Packet-Type == "Access-Accept" {
      update reply {
        &Class += "class1"
        &Class += "class2"
        &Class += "class3"
        &Class += "class4"
        &Class += "class5"
        &Chargeable-User-Identity += "cui1"
        &Acct-Interim-Interval := 10
      }
    }
  }
}

client any {
  ipaddr = 0.0.0.0/0
  proto = udp
  secret = secret
}
_EOF_

ln -fs "$fr_virt_server_file" "$fr_base_dir/sites-enabled/raa"

#Add entry to users file
line_to_add="raauser Cleartext-Password := \"secret\""
file="$fr_base_dir/users"
add_line_to_file "$line_to_add" "$file"

#Make changes to eap module
sed -i 's/^\tdefault_eap_type.*/\tdefault_eap_type = ttls/g' $fr_base_dir/mods-enabled/eap
sed -i 's/^\t\tdefault_eap_type.*/\t\tdefault_eap_type = mschapv2/g' $fr_base_dir/mods-enabled/eap
