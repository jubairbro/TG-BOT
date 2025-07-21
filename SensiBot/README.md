ঠিক আছে, যদি আপনার Xray `config.json` এর লজিক আপনি নিজে ম্যানুয়ালি যোগ করতে চান, তাহলে আপনাকে `/opt/sensi_bot_scripts/` ডিরেক্টরিতে যে স্ক্রিপ্টগুলো আছে, সেগুলোর মধ্যেই এই পরিবর্তনগুলো করতে হবে। এই স্ক্রিপ্টগুলোই Xray কনফিগারেশন ফাইল (`/etc/xray/config.json`) এর সাথে সরাসরি ইন্টারঅ্যাক্ট করবে।

আমি আপনাকে প্রতিটি স্ক্রিপ্টের সেই নির্দিষ্ট অংশগুলো চিহ্নিত করে দিচ্ছি যেখানে Xray `config.json` ম্যানুয়ালি আপডেট করার লজিক বসাতে হবে। আমি আবারও মনে করিয়ে দিচ্ছি, `jq` টুলটি Xray `config.json` ফাইল ম্যানিপুলেট করার জন্য অত্যন্ত উপযোগী। যদি আপনার সিস্টেমে `jq` ইনস্টল করা না থাকে, তাহলে এটি ইনস্টল করে নিন: `sudo apt-get install jq`।

এই পরিবর্তনগুলোর পর সম্পূর্ণ সেটআপ প্রক্রিয়াটিও আমি আবার উল্লেখ করব।

---

### ধাপ ১: পূর্ববর্তী সেটআপ পরিষ্কার করা (যদি না করে থাকেন)

এটি নিশ্চিত করবে যে আপনি একটি পরিষ্কার অবস্থায় শুরু করছেন।

1.  **বট সার্ভিস বন্ধ এবং ডিজেবল করুন:**
    ```bash
    sudo systemctl stop mybot.service
    sudo systemctl disable mybot.service
    sudo rm /etc/systemd/system/mybot.service
    sudo systemctl daemon-reload
    sudo systemctl reset-failed
    ```

2.  **পুরনো বট ফাইল এবং স্ক্রিপ্টগুলো মুছে ফেলুন:**
    ```bash
    sudo rm -rf /root/telegram_bot/
    sudo rm -rf /opt/sensi_bot_scripts/
    ```

---

### ধাপ ২: নতুন ডিরেক্টরি তৈরি করুন এবং `jq` ইনস্টল করুন

1.  **নতুন ডিরেক্টরি তৈরি করুন:**
    ```bash
    sudo mkdir -p /opt/sensi_bot_scripts/
    ```

2.  **`jq` ইনস্টল করুন (যদি না থাকে):**
    ```bash
    sudo apt-get update
    sudo apt-get install -y jq at
    sudo systemctl enable atd --now # Enable and start 'at' service for trial cleanup
    ```

---

### ধাপ ৩: স্বয়ংসম্পূর্ণ ব্যাশ স্ক্রিপ্ট ফাইলগুলো তৈরি এবং Xray লজিক যোগ করা

প্রতিটি কোড ব্লক কপি করে সার্ভারে `/opt/sensi_bot_scripts/` ডিরেক্টরিতে সংশ্লিষ্ট ফাইল নামে সেভ করুন। আমি শুধুমাত্র Xray সম্পর্কিত লজিক যেখানে যোগ করতে হবে, সেই অংশগুলোতেই পরিবর্তন করে দেব। বাকি কোড অপরিবর্তিত থাকবে।

---

**১. `/opt/sensi_bot_scripts/create_account.sh`**

এই ফাইলে Xray প্রোটোকল (vmess, vless, trojan, shadowsocks) এর জন্য নতুন ক্লায়েন্ট যোগ করার লজিক যোগ করতে হবে।

```bash
#!/bin/bash
# /opt/sensi_bot_scripts/create_account.sh
# Creates SSH/Xray account, designed for bot integration with JSON output.

# --- Access check (from your original scripts) ---
data_acc="https://raw.githubusercontent.com/jubairbro/access/refs/heads/main/"
data_key=$(cat /root/.key 2>/dev/null) # Suppress error if .key not found
if [ -z "$data_key" ]; then
    echo '{"status": "error", "message": "Access key not found at /root/.key"}'
    exit 1
fi

status_code=$(curl -s -o /dev/null -w "%{http_code}" "$data_acc$data_key")

if [ "$status_code" -ne 200 ]; then
    echo '{"status": "error", "message": "PERMISSION DENIED! Access key validation failed or server unreachable."}'
    exit 1
fi
expiry_date=$(date -d "$(curl -s "$data_acc$data_key")" +%s)
current_date=$(date +%s)
if [ "$expiry_date" -le "$current_date" ]; then
    echo '{"status": "error", "message": "PERMISSION DENIED! Script access has expired."}'
    exit 1
fi

# --- Arguments ---
protocol="$1"
username="$2"
password="$3" # Used for SSH, dummy for Xray
duration_days="$4"
quota_gb="$5"
ip_limit="$6"

# --- Input Validation ---
if [ -z "$protocol" ] || [ -z "$username" ] || [ -z "$duration_days" ] || [ -z "$quota_gb" ] || [ -z "$ip_limit" ]; then
    echo '{"status": "error", "message": "Missing arguments. Usage: create_account.sh <protocol> <username> <password> <days> <quota_gb> <ip_limit>"}'
    echo '{"status": "error", "message": "Missing arguments."}'
    exit 1
fi
if ! [[ "$duration_days" =~ ^[0-9]+$ ]] || ! [[ "$quota_gb" =~ ^[0-9]+$ ]] || ! [[ "$ip_limit" =~ ^[0-9]+$ ]]; then
    echo '{"status": "error", "message": "Days, quota, and IP limit must be numbers."}'
    exit 1
fi

# Sanitize username (from your original script)
username=$(echo "$username" | tr -dc 'a-zA-Z0-9_-')
if [[ ${#username} -lt 3 ]]; then
    echo '{"status": "error", "message": "Username must be at least 3 characters and alphanumeric/hyphen/underscore."}'
    exit 1
fi

# --- Global variables (from your original script) ---
ip=$(wget -qO- ipv4.icanhazip.com 2>/dev/null || curl -s ipv4.icanhazip.com 2>/dev/null || echo "N/A")
city=$(cat /etc/xray/city 2>/dev/null || echo "Unknown city")
pubkey=$(cat /etc/slowdns/server.pub 2>/dev/null || echo "Pubkey not available")
ns_domain=$(cat /etc/xray/dns 2>/dev/null || echo "NS domain not set")
domain=$(cat /etc/xray/domain 2>/dev/null || hostname -f)

expiration_date_for_useradd=$(date -d "+$duration_days days" +"%Y-%m-%d")
exp_formatted=$(date -d "+$duration_days days" +"%Y-%m-%d %H:%M:%S")

user_uuid=""
# Xray UUID generation
if [[ "$protocol" != "ssh" ]]; then
    user_uuid=$(cat /proc/sys/kernel/random/uuid)
fi

# --- Account creation logic based on protocol ---
case "$protocol" in
    ssh)
        # Check for existing user in SSH DB
        if grep -q "^### $username " "/etc/ssh/.ssh.db" 2>/dev/null; then
            echo '{"status": "error", "message": "SSH username already exists."}'
            exit 1
        fi

        useradd -e "$expiration_date_for_useradd" -s /bin/false -M "$username" >/dev/null 2>&1
        if [ $? -ne 0 ]; then echo '{"status": "error", "message": "Failed to add SSH system user."}'; exit 1; fi
        
        echo -e "$password\n$password\n" | passwd "$username" >/dev/null 2>&1
        if [ $? -ne 0 ]; then userdel -f "$username" >/dev/null 2>&1; echo '{"status": "error", "message": "Failed to set SSH user password."}'; exit 1; fi
        
        # IP limit for SSH
        mkdir -p /etc/ssh/ >/dev/null 2>&1
        if [[ "$ip_limit" != "0" ]]; then
            echo "$ip_limit" > "/etc/ssh/${username}"
        fi
        echo "### ${username} ${exp_formatted}" >> "/etc/ssh/.ssh.db"

        cat <<EOF
{
    "status": "success",
    "message": "SSH Account Created",
    "data": {
        "protocol": "ssh",
        "username": "$username",
        "password": "$password",
        "expiration": "$exp_formatted",
        "ip_limit": "$ip_limit",
        "ip": "$ip",
        "host": "$domain",
        "slowdns_host": "$ns_domain",
        "location": "$city",
        "openssh_port": "443, 80, 22",
        "udpssh_port": "1-65535",
        "dropbear_port": "443, 109",
        "ssh_ws_port": "80",
        "ssh_ssl_ws_port": "443",
        "ssl_tls_port": "443",
        "ovpn_ssl_port": "443",
        "ovpn_tcp_port": "1194",
        "ovpn_udp_port": "2200",
        "badvpn_udp": "7100, 7300, 7300",
        "public_key": "$pubkey",
        "wss_payload": "GET / HTTP/1.1[crlf]Host: [host][crlf]Upgrade: websocket[crlf][crlf]",
        "openvpn_link": "http://$domain:85",
        "save_account_link": "https://$domain:81/ssh-$username.txt"
    }
}
EOF
        ;;
    vmess|vless|trojan|shadowsocks)
        XRAY_CONFIG_FILE="/etc/xray/config.json"
        
        # Ensure jq is installed
        if ! command -v jq &>/dev/null; then
            echo '{"status": "error", "message": "jq is not installed. Please install it (apt install jq)."}'
            exit 1
        fi

        mkdir -p "/etc/xray/$protocol" >/dev/null 2>&1
        if grep -q "^### $username " "/etc/xray/$protocol/.$protocol.db" 2>/dev/null; then
            echo '{"status": "error", "message": "'"$protocol"' username already exists."}'
            exit 1
        fi

        echo "### $username $exp_formatted $quota_gb $ip_limit $user_uuid" >> "/etc/xray/$protocol/.$protocol.db"

        # --- ACTUAL XRAY CONFIG MODIFICATION LOGIC HERE ---
        # This is a common structure. Adjust 'tag' values and inbound settings if yours are different.
        # Ensure your config.json has inbounds with these 'tags' and a 'clients' array.
        temp_config=$(jq --argjson new_client '{"id": "'"$user_uuid"'", "email": "'"$username"'", "level": 0}' \
            '(.inbounds[] | select(.tag == "'"$protocol"'-ws").settings.clients) |= . + [$new_client] | 
             (.inbounds[] | select(.tag == "'"$protocol"'-grpc").settings.clients) |= . + [$new_client]' \
            "$XRAY_CONFIG_FILE")
        
        if [ $? -ne 0 ]; then
            echo '{"status": "error", "message": "Failed to update Xray config with new client. Check config.json structure or jq command."}'
            echo "$temp_config" >&2 # Output jq error for debugging
            exit 1
        fi
        
        echo "$temp_config" | jq . > "$XRAY_CONFIG_FILE.tmp" && mv "$XRAY_CONFIG_FILE.tmp" "$XRAY_CONFIG_FILE"
        if [ $? -ne 0 ]; then
            echo '{"status": "error", "message": "Failed to write Xray config file after adding client."}'
            exit 1
        fi
        
        # --- End of Xray config modification logic ---

        # Generate links (ensure these reflect your actual Xray configuration)
        vmess_tls_link="vmess://${user_uuid}@${domain}:443?path=%2Fvmess&security=tls&encryption=none&type=ws#${username}_TLS"
        vmess_nontls_link="vmess://${user_uuid}@${domain}:80?path=%2Fvmess&security=none&encryption=none&type=ws#${username}_HTTP"
        vmess_grpc_link="vmess://${user_uuid}@${domain}:443?mode=gun&security=tls&serviceName=vmess&type=grpc#${username}_gRPC"
        
        vless_tls_link="vless://${user_uuid}@${domain}:443?path=%2Fvless&security=tls&encryption=none&type=ws#${username}_TLS"
        vless_nontls_link="vless://${user_uuid}@${domain}:80?path=%2Fvless&security=none&encryption=none&type=ws#${username}_HTTP"
        vless_grpc_link="vless://${user_uuid}@${domain}:443?mode=gun&security=tls&serviceName=vless&type=grpc#${username}_gRPC"

        trojan_tls_link="trojan://${user_uuid}@${domain}:443?security=tls&type=ws#${username}_TLS"
        trojan_grpc_link="trojan://${user_uuid}@${domain}:443?mode=gun&security=tls&serviceName=trojan&type=grpc#${username}_gRPC"

        ss_cipher="chacha20-poly1305" # Common cipher, adjust if yours is different
        ss_base64_password_port=$(echo -n "${ss_cipher}:${user_uuid}@${domain}:443" | base64 -w0)
        ss_link_ws="ss://${ss_base64_password_port}?path=%2Fss&security=tls&type=ws#${username}_WS"
        ss_link_grpc="ss://${ss_base64_password_port}?mode=gun&security=tls&serviceName=ss&type=grpc#${username}_gRPC"


        systemctl restart "xray@$protocol" >/dev/null 2>&1
        if [ $? -ne 0 ]; then
            echo '{"status": "error", "message": "Failed to restart Xray service for '"$protocol"'."}'
            exit 1
        fi

        cat <<EOF
{
    "status": "success",
    "message": "$protocol Account Created",
    "data": {
        "protocol": "$protocol",
        "username": "$username",
        "uuid": "$user_uuid",
        "expiration": "$exp_formatted",
        "quota_gb": "$quota_gb",
        "ip_limit": "$ip_limit",
        "ip": "$ip",
        "host": "$domain",
        "slowdns_host": "$ns_domain",
        "location": "$city",
        "openssh_port": "443, 80, 22",
        "ssl_tls_port": "443",
        "vmess_tls_link": "$vmess_tls_link",
        "vmess_nontls_link": "$vmess_nontls_link",
        "vmess_grpc_link": "$vmess_grpc_link",
        "vless_tls_link": "$vless_tls_link",
        "vless_nontls_link": "$vless_nontls_link",
        "vless_grpc_link": "$vless_grpc_link",
        "trojan_tls_link": "$trojan_tls_link",
        "trojan_grpc_link": "$trojan_grpc_link",
        "ss_link_ws": "$ss_link_ws",
        "ss_link_grpc": "$ss_link_grpc"
    }
}
EOF
        ;;
    *)
        echo '{"status": "error", "message": "Invalid protocol specified."}'
        exit 1
        ;;
esac
exit 0
```

---

**২. `/opt/sensi_bot_scripts/delete_account.sh`**

এই ফাইলে Xray প্রোটোকলের জন্য ক্লায়েন্ট সরানোর লজিক যোগ করতে হবে।

```bash
#!/bin/bash
# /opt/sensi_bot_scripts/delete_account.sh
# Deletes SSH/Xray account or lists users, designed for bot integration with JSON output.

# --- Access check ---
data_acc="https://raw.githubusercontent.com/jubairbro/access/refs/heads/main/"
data_key=$(cat /root/.key 2>/dev/null)
if [ -z "$data_key" ]; then echo '{"status": "error", "message": "Access key not found at /root/.key"}'; exit 1; fi
status_code=$(curl -s -o /dev/null -w "%{http_code}" "$data_acc$data_key")
if [ "$status_code" -ne 200 ]; then echo '{"status": "error", "message": "PERMISSION DENIED! Access key validation failed."}'; exit 1; fi
expiry_date=$(date -d "$(curl -s "$data_acc$data_key")" +%s)
current_date=$(date +%s)
if [ "$expiry_date" -le "$current_date" ]; then echo '{"status": "error", "message": "PERMISSION DENIED! Script access has expired."}'; exit 1; fi

# --- Arguments ---
protocol="$1"
username="$2" # Optional

# --- Input Validation ---
if [ -z "$protocol" ]; then
    echo '{"status": "error", "message": "Usage: delete_account.sh <protocol> [username]"}'
    exit 1
fi

# --- Logic ---
if [ -z "$username" ]; then
    # List users
    case "$protocol" in
        ssh)
            if [ -f "/etc/ssh/.ssh.db" ]; then
                users=($(grep "^###" "/etc/ssh/.ssh.db" | awk '{print $2}'))
                json_users=$(printf '%s\n' "${users[@]}" | jq -R . | jq -s .)
                echo '{"status": "success", "message": "SSH users listed.", "users": '$json_users'}'
            else
                echo '{"status": "success", "message": "No SSH users found.", "users": []}'
            fi
            ;;
        vmess|vless|trojan|shadowsocks)
            db_file="/etc/xray/$protocol/.$protocol.db"
            if [ -f "$db_file" ]; then
                users=($(grep "^###" "$db_file" | awk '{print $2}'))
                json_users=$(printf '%s\n' "${users[@]}" | jq -R . | jq -s .)
                echo '{"status": "success", "message": "'"$protocol"' users listed.", "users": '$json_users'}'
            else
                echo '{"status": "success", "message": "No '"$protocol"' users found.", "users": []}'
            fi
            ;;
        *)
            echo '{"status": "error", "message": "Invalid protocol for listing users."}'
            exit 1
            ;;
    esac
else
    # Delete user
    case "$protocol" in
        ssh)
            if ! grep -q "^### $username " "/etc/ssh/.ssh.db" 2>/dev/null; then
                echo '{"status": "error", "message": "SSH username '"$username"' not found."}'
                exit 1
            fi
            userdel -f "$username" >/dev/null 2>&1
            rm -f "/etc/ssh/${username}" "/etc/ssh/.ssh.db_history" >/dev/null 2>&1
            sed -i "/^### $username /d" "/etc/ssh/.ssh.db" >/dev/null 2>&1
            echo '{"status": "success", "message": "SSH user '"$username"' deleted."}'
            ;;
        vmess|vless|trojan|shadowsocks)
            db_file="/etc/xray/$protocol/.$protocol.db"
            XRAY_CONFIG_FILE="/etc/xray/config.json"
            
            if ! grep -q "^### $username " "$db_file" 2>/dev/null; then
                echo '{"status": "error", "message": "'"$protocol"' username '"$username"' not found."}'
                exit 1
            fi
            
            # Get UUID for deletion
            user_uuid=$(grep "^### $username " "$db_file" | awk '{print $NF}' | head -n 1)

            # Ensure jq is installed
            if ! command -v jq &>/dev/null; then
                echo '{"status": "error", "message": "jq is not installed. Please install it (apt install jq)."}'
                exit 1
            fi
            
            # --- ACTUAL XRAY CONFIG MODIFICATION LOGIC HERE ---
            # Remove client from Xray config.json
            # This assumes a common Xray config structure with an array of inbounds,
            # and each inbound having a .settings.clients array.
            # Adjust 'tag' values if yours are different.
            temp_config=$(jq 'walk(if type == "object" and has("id") and .id == "'"$user_uuid"'" then empty else . end)' \
                          "$XRAY_CONFIG_FILE")
            
            if [ $? -ne 0 ]; then
                echo '{"status": "error", "message": "Failed to remove client from Xray config. Check config.json structure or jq command."}'
                echo "$temp_config" >&2 # Output jq error for debugging
                exit 1
            fi
            echo "$temp_config" | jq . > "$XRAY_CONFIG_FILE.tmp" && mv "$XRAY_CONFIG_FILE.tmp" "$XRAY_CONFIG_FILE"
            if [ $? -ne 0 ]; then
                echo '{"status": "error", "message": "Failed to write Xray config file after deleting client."}'
                exit 1
            fi

            sed -i "/^### $username /d" "$db_file" >/dev/null 2>&1
            echo '{"status": "success", "message": "'"$protocol"' user '"$username"' deleted."}'
            systemctl restart "xray@$protocol" >/dev/null 2>&1
            if [ $? -ne 0 ]; then
                echo '{"status": "error", "message": "Failed to restart Xray service for '"$protocol"' after deletion."}'
                exit 1
            fi
            ;;
        *)
            echo '{"status": "error", "message": "Invalid protocol for deleting user."}'
            exit 1
            ;;
    esac
    exit 0
```

---

**৩. `/opt/sensi_bot_scripts/renew_account.sh`**

এই ফাইলে Xray প্রোটোকলের জন্য রিনিউ করার লজিক যোগ করতে হবে।

```bash
#!/bin/bash
# /opt/sensi_bot_scripts/renew_account.sh
# Renews SSH/Xray account, designed for bot integration with JSON output.

# --- Access check ---
data_acc="https://raw.githubusercontent.com/jubairbro/access/refs/heads/main/"
data_key=$(cat /root/.key 2>/dev/null)
if [ -z "$data_key" ]; then echo '{"status": "error", "message": "Access key not found at /root/.key"}'; exit 1; fi
status_code=$(curl -s -o /dev/null -w "%{http_code}" "$data_acc$data_key")
if [ "$status_code" -ne 200 ]; then echo '{"status": "error", "message": "PERMISSION DENIED! Access key validation failed."}'; exit 1; fi
expiry_date=$(date -d "$(curl -s "$data_acc$data_key")" +%s)
current_date=$(date +%s)
if [ "$expiry_date" -le "$current_date" ]; then echo '{"status": "error", "message": "PERMISSION DENIED! Script access has expired."}'; exit 1; fi

# --- Arguments ---
protocol="$1"
username="$2"
add_days="$3"
new_quota_gb="$4"
new_ip_limit="$5"

# --- Input Validation ---
if [ -z "$protocol" ] || [ -z "$username" ] || [ -z "$add_days" ] || [ -z "$new_quota_gb" ] || [ -z "$new_ip_limit" ]; then
    echo '{"status": "error", "message": "Usage: renew_account.sh <protocol> <username> <add_days> <new_quota_gb> <new_ip_limit>"}'
    exit 1
fi
if ! [[ "$add_days" =~ ^[0-9]+$ ]] || ! [[ "$new_quota_gb" =~ ^[0-9]+$ ]] || ! [[ "$new_ip_limit" =~ ^[0-9]+$ ]]; then
    echo '{"status": "error", "message": "Add days, new quota, and new IP limit must be numbers."}'
    exit 1
fi

# --- Logic ---
case "$protocol" in
    ssh)
        if ! grep -q "^### $username " "/etc/ssh/.ssh.db" 2>/dev/null; then
            echo '{"status": "error", "message": "SSH username '"$username"' not found."}'
            exit 1
        fi
        
        # Renew SSH user expiry
        current_expiry_str=$(chage -l "$username" 2>/dev/null | grep "Account expires" | awk -F": " '{print $2}')
        if [ -z "$current_expiry_str" ] || [ "$current_expiry_str" == "never" ]; then
            current_expiry_timestamp=$(date +%s) # Treat as now if no current expiry
        else
            current_expiry_timestamp=$(date -d "$current_expiry_str" +%s 2>/dev/null || date +%s)
        fi
        
        new_expiry_timestamp=$(( current_expiry_timestamp + add_days * 86400 ))
        new_expiry_date_useradd=$(date -d "@$new_expiry_timestamp" +"%Y-%m-%d")
        new_exp_formatted=$(date -d "@$new_expiry_timestamp" +"%Y-%m-%d %H:%M:%S")

        usermod -e "$new_expiry_date_useradd" "$username" >/dev/null 2>&1
        if [ $? -ne 0 ]; then echo '{"status": "error", "message": "Failed to update SSH user expiry."}'; exit 1; fi

        # Update IP limit for SSH
        mkdir -p /etc/ssh/ >/dev/null 2>&1
        if [[ "$new_ip_limit" != "0" ]]; then
            echo "$new_ip_limit" > "/etc/ssh/${username}"
        else
            rm -f "/etc/ssh/${username}" >/dev/null 2>&1 # Remove limit file if 0
        fi
        sed -i "/^### $username /c\### $username ${new_exp_formatted}" "/etc/ssh/.ssh.db" >/dev/null 2>&1

        echo '{"status": "success", "message": "SSH user '"$username"' renewed.", "data": {"username": "'"$username"'", "exp": "'"$new_exp_formatted"'", "limitip": "'"$new_ip_limit"'"}}'
        ;;
    vmess|vless|trojan|shadowsocks)
        db_file="/etc/xray/$protocol/.$protocol.db"
        if ! grep -q "^### $username " "$db_file" 2>/dev/null; then
            echo '{"status": "error", "message": "'"$protocol"' username '"$username"' not found."}'
            exit 1
        fi
        # --- Xray Renewal Logic (Adapt from your original apirenew / renewvmess etc.) ---
        # This involves:
        # 1. Reading current user data from .db file (username, old_expiry, old_quota, old_ip_limit, uuid).
        # 2. Calculating new expiry date.
        # 3. Updating the user entry in /etc/xray/<protocol>/.<protocol>.db.
        # 4. Updating Xray config.json (if quota/limit directly managed there, often not).
        # 5. Restarting the relevant Xray service.

        # Example: Retrieve current info from DB
        line_data=$(grep "^### $username " "$db_file" | head -n 1)
        old_exp_str=$(echo "$line_data" | awk '{print $3, $4}') # This might be wrong depending on your .db format
        old_quota=$(echo "$line_data" | awk '{print $5}')
        old_ip_limit=$(echo "$line_data" | awk '{print $6}')
        user_uuid=$(echo "$line_data" | awk '{print $NF}')
        
        # Calculate new expiry:
        old_exp_timestamp=$(date -d "$old_exp_str" +%s 2>/dev/null || date +%s)
        new_exp_timestamp=$(( old_exp_timestamp + add_days * 86400 ))
        new_exp_formatted=$(date -d "@$new_exp_timestamp" +"%Y-%m-%d %H:%M:%S")

        # Update DB entry
        sed -i "/^### $username /c\### $username ${new_exp_formatted} ${new_quota_gb} ${new_ip_limit} ${user_uuid}" "$db_file" >/dev/null 2>&1

        echo '{"status": "success", "message": "'"$protocol"' user '"$username"' renewed.", "data": {"username": "'"$username"'", "exp": "'"$new_exp_formatted"'", "quota": "'"$new_quota_gb"'", "limitip": "'"$new_ip_limit"'"}}'
        systemctl restart "xray@$protocol" >/dev/null 2>&1
        if [ $? -ne 0 ]; then
            echo '{"status": "error", "message": "Failed to restart Xray service for '"$protocol"' after renewal."}'
            exit 1
        fi
        ;;
    *)
        echo '{"status": "error", "message": "Invalid protocol for renewal."}'
        exit 1
        ;;
esac
exit 0
```

---

**৪. `/opt/sensi_bot_scripts/check_account.sh`**

এই ফাইলে Xray প্রোটোকলের জন্য সক্রিয় সংযোগ এবং ব্যবহারের তথ্য যাচাই করার লজিক যোগ করতে হবে।

```bash
#!/bin/bash
# /opt/sensi_bot_scripts/check_account.sh
# Checks active connections for SSH/Xray protocols, designed for bot integration with JSON output.

# --- Access check ---
data_acc="https://raw.githubusercontent.com/jubairbro/access/refs/heads/main/"
data_key=$(cat /root/.key 2>/dev/null)
if [ -z "$data_key" ]; then echo '{"status": "error", "message": "Access key not found at /root/.key"}'; exit 1; fi
status_code=$(curl -s -o /dev/null -w "%{http_code}" "$data_acc$data_key")
if [ "$status_code" -ne 200 ]; then echo '{"status": "error", "message": "PERMISSION DENIED! Access key validation failed."}'; exit 1; fi
expiry_date=$(date -d "$(curl -s "$data_acc$data_key")" +%s)
current_date=$(date +%s)
if [ "$expiry_date" -le "$current_date" ]; then echo '{"status": "error", "message": "PERMISSION DENIED! Script access has expired."}'; exit 1; fi

# --- Arguments ---
protocol="$1"

# --- Input Validation ---
if [ -z "$protocol" ]; then
    echo '{"status": "error", "message": "Usage: check_account.sh <protocol>"}'
    exit 1
fi

# --- Logic ---
json_output_data="[]" # Default empty array

case "$protocol" in
    ssh)
        # Replicate your SSH connection check logic (from /usr/bin/apicheck or similar)
        if [ -f "/etc/ssh/.ssh.db" ]; then
            users=($(grep "^###" "/etc/ssh/.ssh.db" | awk '{print $2}'))
            temp_json_array=""
            for user_entry in "${users[@]}"; do
                active_sessions=$(who | grep -w "$user_entry" | wc -l)
                limit_ip=$(cat "/etc/ssh/${user_entry}" 2>/dev/null || echo "0")
                db_line=$(grep "^### $user_entry " "/etc/ssh/.ssh.db" 2>/dev/null)
                
                if [ -z "$db_line" ]; then
                    expiry="N/A"
                else
                    expiry=$(echo "$db_line" | awk '{print $3, $4}')
                fi
                
                usage="0B"  # Placeholder: Implement actual SSH usage tracking if available
                quota="0GB" # Placeholder: Implement actual SSH quota if available

                temp_json_array+='{"user": "'"$user_entry"'", "usage": "'"$usage"'", "quota": "'"$quota"'", "ip_limit": "'"$limit_ip"'", "ip_count": "'"$active_sessions"'", "log_count": "N/A", "expiration": "'"$expiry"'"}'
                temp_json_array+=","
            done
            if [ -n "$temp_json_array" ]; then
                json_output_data="[${temp_json_array%,}]" # Remove trailing comma
            fi
        fi
        echo '{"status": "success", "message": "SSH accounts checked.", "data": '$json_output_data'}'
        ;;
    vmess|vless|trojan|shadowsocks)
        db_file="/etc/xray/$protocol/.$protocol.db"
        if [ -f "$db_file" ]; then
            users_data=($(grep "^###" "$db_file"))
            temp_json_array=""
            for line in "${users_data[@]}"; do
                user_entry=$(echo "$line" | awk '{print $2}')
                exp=$(echo "$line" | awk '{print $3, $4}')
                quota=$(echo "$line" | awk '{print $5}')
                limit=$(echo "$line" | awk '{print $6}')
                user_uuid=$(echo "$line" | awk '{print $NF}')

                # --- Xray Connection/Usage Check Logic (Adapt from your original apicheck) ---
                # This is complex and depends heavily on your Xray configuration and logging.
                # You might need to parse Xray access logs, or use Xray's API for stats.
                # Example for connections (very basic, might not be accurate for all setups):
                # active_connections=$(ss -tunap | grep ":443" | grep "$ip_of_user_or_xray_bind_ip" | wc -l)
                # For per-user usage, Xray's API is ideal if enabled.
                
                # Placeholder values:
                active_connections="0" # Implement actual active connection check for Xray
                current_usage="0GB"    # Implement actual data usage calculation for Xray
                
                temp_json_array+='{"user": "'"$user_entry"'", "usage": "'"$current_usage"'", "quota": "'"$quota"'", "ip_limit": "'"$limit"'", "ip_count": "'"$active_connections"'", "log_count": "N/A", "expiration": "'"$exp"'", "uuid": "'"$user_uuid"'"}'
                temp_json_array+=","
            done
            if [ -n "$temp_json_array" ]; then
                json_output_data="[${temp_json_array%,}]"
            fi
        fi
        echo '{"status": "success", "message": "'"$protocol"' accounts checked.", "data": '$json_output_data'}'
        ;;
    *)
        echo '{"status": "error", "message": "Invalid protocol for checking."}'
        exit 1
        ;;
esac
exit 0
```

---

**৫. `/opt/sensi_bot_scripts/create_trial_account.sh`**

এই ফাইলে Xray প্রোটোকলের জন্য ট্রায়াল অ্যাকাউন্ট তৈরির লজিক যোগ করতে হবে।

```bash
#!/bin/bash
# /opt/sensi_bot_scripts/create_trial_account.sh
# Creates trial SSH/Xray account, designed for bot integration with JSON output.

# --- Access check ---
data_acc="https://raw.githubusercontent.com/jubairbro/access/refs/heads/main/"
data_key=$(cat /root/.key 2>/dev/null)
if [ -z "$data_key" ]; then echo '{"status": "error", "message": "Access key not found at /root/.key"}'; exit 1; fi
status_code=$(curl -s -o /dev/null -w "%{http_code}" "$data_acc$data_key")
if [ "$status_code" -ne 200 ]; then echo '{"status": "error", "message": "PERMISSION DENIED! Access key validation failed."}'; exit 1; fi
expiry_date=$(date -d "$(curl -s "$data_acc$data_key")" +%s)
current_date=$(date +%s)
if [ "$expiry_date" -le "$current_date" ]; then echo '{"status": "error", "message": "PERMISSION DENIED! Script access has expired."}'; exit 1; fi

# --- Arguments ---
protocol="$1"
duration_minutes="$2"

# --- Input Validation ---
if [ -z "$protocol" ] || [ -z "$duration_minutes" ]; then
    echo '{"status": "error", "message": "Usage: create_trial_account.sh <protocol> <duration_minutes>"}'
    exit 1
fi
if ! [[ "$duration_minutes" =~ ^[0-9]+$ ]] || [ "$duration_minutes" -le 0 ]; then
    echo '{"status": "error", "message": "Duration (minutes) must be a positive number."}'
    exit 1
fi

# Generate random username (from your original trial scripts)
username=$(head /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 8 | head -n 1)

# --- Global variables ---
ip=$(wget -qO- ipv4.icanhazip.com 2>/dev/null || curl -s ipv4.icanhazip.com 2>/dev/null || echo "N/A")
city=$(cat /etc/xray/city 2>/dev/null || echo "Unknown city")
pubkey=$(cat /etc/slowdns/server.pub 2>/dev/null || echo "Pubkey not available")
ns_domain=$(cat /etc/xray/dns 2>/dev/null || echo "NS domain not set")
domain=$(cat /etc/xray/domain 2>/dev/null || hostname -f)

expiration_time_string=$(date -d "+$duration_minutes minutes" +"%Y-%m-%d %H:%M:%S")
expiration_date_for_useradd=$(date -d "+$duration_minutes minutes" +"%Y-%m-%d")

user_uuid=""
if [[ "$protocol" != "ssh" ]]; then
    user_uuid=$(cat /proc/sys/kernel/random/uuid)
fi

# --- Account creation logic based on protocol ---
case "$protocol" in
    ssh)
        # Check for existing user (though trials are usually unique)
        if grep -q "^### $username " "/etc/ssh/.ssh.db" 2>/dev/null || grep -q "^### $username " "/etc/ssh/.ssh.db_trial" 2>/dev/null; then
            echo '{"status": "error", "message": "Generated trial username already exists. Try again."}'
            exit 1
        fi

        useradd -e "$expiration_date_for_useradd" -s /bin/false -M "$username" >/dev/null 2>&1
        if [ $? -ne 0 ]; then echo '{"status": "error", "message": "Failed to add SSH trial user."}'; exit 1; fi
        echo "$username:$username" | chpasswd >/dev/null 2>&1
        if [ $? -ne 0 ]; then userdel -f "$username" >/dev/null 2>&1; echo '{"status": "error", "message": "Failed to set SSH trial password."}'; exit 1; fi

        # Register cleanup for trial account using 'at' command
        # Ensure 'at' service is installed and running (apt install at; systemctl enable atd --now)
        echo "/opt/sensi_bot_scripts/cleanup_trial_account.sh ssh $username" | at now + "$duration_minutes" minutes 2>/dev/null
        if [ $? -ne 0 ]; then
            echo '{"status": "warning", "message": "Failed to schedule auto-deletion for SSH trial account. Make sure `at` service is running."}' >&2
        fi
        
        echo "### $username $expiration_time_string" >> "/etc/ssh/.ssh.db_trial" # Separate DB for trials

        cat <<EOF
{
    "status": "success",
    "message": "Trial SSH Account Created",
    "data": {
        "protocol": "ssh",
        "username": "$username",
        "password": "$username",
        "expiration": "$expiration_time_string",
        "ip": "$ip",
        "host": "$domain",
        "slowdns_host": "$ns_domain",
        "location": "$city",
        "openssh_port": "443, 80, 22",
        "save_account_link": "https://$domain:81/ssh-$username.txt"
    }
}
EOF
        ;;
    vmess|vless|trojan|shadowsocks)
        XRAY_CONFIG_FILE="/etc/xray/config.json"

        # Ensure jq is installed
        if ! command -v jq &>/dev/null; then
            echo '{"status": "error", "message": "jq is not installed. Please install it (apt install jq)."}'
            exit 1
        fi

        mkdir -p "/etc/xray/$protocol" >/dev/null 2>&1
        if grep -q "^### $username " "/etc/xray/$protocol/.$protocol.db_trial" 2>/dev/null; then
            echo '{"status": "error", "message": "Generated trial '"$protocol"' username already exists. Try again."}'
            exit 1
        fi

        echo "### $username $expiration_time_string 0 1 $user_uuid" >> "/etc/xray/$protocol/.$protocol.db_trial" # Quota 0, IP limit 1 for trial

        # Add client to Xray config.json (trial)
        inbound_path=""
        case "$protocol" in
            vmess) inbound_path='.inbounds[] | select(.tag == "vmess-ws" or .tag == "vmess-grpc")' ;;
            vless) inbound_path='.inbounds[] | select(.tag == "vless-ws" or .tag == "vless-grpc")' ;;
            trojan) inbound_path='.inbounds[] | select(.tag == "trojan-ws" or .tag == "trojan-grpc")' ;;
            shadowsocks) inbound_path='.inbounds[] | select(.tag == "shadowsocks-ws" or .tag == "shadowsocks-grpc")' ;;
        esac
        
        temp_config=$(jq --argjson new_client '{"id": "'"$user_uuid"'", "email": "'"$username"'_trial", "level": 0}' \
            "$inbound_path | .settings.clients += [$new_client]" \
            "$XRAY_CONFIG_FILE")

        if [ $? -ne 0 ]; then
            echo '{"status": "error", "message": "Failed to update Xray config with new trial client. Check config.json structure or jq command."}'
            echo "$temp_config" >&2 # Output jq error for debugging
            exit 1
        fi
        
        echo "$temp_config" | jq . > "$XRAY_CONFIG_FILE.tmp" && mv "$XRAY_CONFIG_FILE.tmp" "$XRAY_CONFIG_FILE"
        if [ $? -ne 0 ]; then
            echo '{"status": "error", "message": "Failed to write Xray config file after adding trial client."}'
            exit 1
        fi

        # Register cleanup for trial account using 'at' command
        echo "/opt/sensi_bot_scripts/cleanup_trial_account.sh $protocol $username" | at now + "$duration_minutes" minutes 2>/dev/null
        if [ $? -ne 0 ]; then
            echo '{"status": "warning", "message": "Failed to schedule auto-deletion for '"$protocol"' trial account. Make sure `at` service is running."}' >&2
        fi
        
        # Generate links (ensure these reflect your actual Xray configuration)
        vmess_tls_link="vmess://${user_uuid}@${domain}:443?path=%2Fvmess&security=tls&encryption=none&type=ws#${username}_TLS_Trial"
        vmess_nontls_link="vmess://${user_uuid}@${domain}:80?path=%2Fvmess&security=none&encryption=none&type=ws#${username}_HTTP_Trial"
        
        systemctl restart "xray@$protocol" >/dev/null 2>&1
        if [ $? -ne 0 ]; then
            echo '{"status": "error", "message": "Failed to restart Xray service for '"$protocol"' trial."}'
            exit 1
        fi
        
        cat <<EOF
{
    "status": "success",
    "message": "Trial $protocol Account Created",
    "data": {
        "protocol": "$protocol",
        "username": "$username",
        "uuid": "$user_uuid",
        "expiration": "$expiration_time_string",
        "ip": "$ip",
        "host": "$domain",
        "slowdns_host": "$ns_domain",
        "location": "$city",
        "vmess_tls_link": "$vmess_tls_link",
        "vmess_nontls_link": "$vmess_nontls_link"
        # Add other trial protocol links here (vless, trojan, ss)
    }
}
EOF
        ;;
    *)
        echo '{"status": "error", "message": "Invalid protocol specified."}'
        exit 1
        ;;
esac
exit 0
```

---

**৬. `/opt/sensi_bot_scripts/cleanup_trial_account.sh`**

এই স্ক্রিপ্টটি ট্রায়াল অ্যাকাউন্ট অটো-ডিলিট করার জন্য `at` কমান্ড দ্বারা কল করা হবে।

```bash
#!/bin/bash
# /opt/sensi_bot_scripts/cleanup_trial_account.sh
# Cleans up trial accounts after their expiry. Called by 'at' command.

protocol="$1"
username="$2"

LOG_FILE="/var/log/sensi_trial_cleanup.log"
echo "$(date): Attempting to clean up $protocol trial account: $username" >> "$LOG_FILE"

# Access check is skipped here for cron/at jobs for simplicity, assuming
# this script is only run by root with proper permissions.

case "$protocol" in
    ssh)
        userdel -f "$username" >/dev/null 2>&1
        rm -f "/etc/ssh/${username}" >/dev/null 2>&1 # Remove IP limit file
        sed -i "/^### $username /d" "/etc/ssh/.ssh.db_trial" >/dev/null 2>&1
        echo "$(date): SSH trial account $username deleted." >> "$LOG_FILE"
        ;;
    vmess|vless|trojan|shadowsocks)
        db_file="/etc/xray/$protocol/.$protocol.db_trial"
        XRAY_CONFIG_FILE="/etc/xray/config.json"

        user_uuid=$(grep "^### $username " "$db_file" | awk '{print $NF}' | head -n 1)

        if [ -n "$user_uuid" ]; then
            # Ensure jq is installed
            if ! command -v jq &>/dev/null; then
                echo "$(date): jq is not installed, cannot cleanup Xray trial $username." >> "$LOG_FILE"
                exit 1
            fi
            
            # Remove client from Xray config.json (trial)
            temp_config=$(jq 'walk(if type == "object" and has("id") and .id == "'"$user_uuid"'" then empty else . end)' \
                          "$XRAY_CONFIG_FILE")
            
            if [ $? -eq 0 ]; then
                echo "$temp_config" | jq . > "$XRAY_CONFIG_FILE.tmp" && mv "$XRAY_CONFIG_FILE.tmp" "$XRAY_CONFIG_FILE"
                sed -i "/^### $username /d" "$db_file" >/dev/null 2>&1
                systemctl restart "xray@$protocol" >/dev/null 2>&1
                echo "$(date): Xray trial account $username ($user_uuid) for $protocol deleted." >> "$LOG_FILE"
            else
                echo "$(date): Failed to remove $protocol client $username ($user_uuid) from Xray config." >> "$LOG_FILE"
            fi
        else
            echo "$(date): Xray trial account $username not found in DB or UUID missing." >> "$LOG_FILE"
        fi
        ;;
    *)
        echo "$(date): Unknown protocol $protocol for cleanup." >> "$LOG_FILE"
        ;;
esac
exit 0
```

---

**৭. `/opt/sensi_bot_scripts/system_actions.sh`**

এই ফাইলটি সিস্টেম-সম্পর্কিত কমান্ডগুলি চালাবে। এটিতে কোনো Xray `config.json` আপডেটের প্রয়োজন নেই, কারণ `change_domain` এর মতো ফাংশনগুলো ইতিমধ্যেই `acme.sh` এর মাধ্যমে সার্টিফিকেট এবং `haproxy` কনফিগারেশন হ্যান্ডেল করে।

```bash
#!/bin/bash
# /opt/sensi_bot_scripts/system_actions.sh
# Executes system-level actions and provides JSON or plain text output.

# --- Access check ---
data_acc="https://raw.githubusercontent.com/jubairbro/access/refs/heads/main/"
data_key=$(cat /root/.key 2>/dev/null)
if [ -z "$data_key" ]; then echo "PERMISSION DENIED! Access key not found at /root/.key"; exit 1; fi
status_code=$(curl -s -o /dev/null -w "%{http_code}" "$data_acc$data_key")
if [ "$status_code" -ne 200 ]; then echo "PERMISSION DENIED! Access key validation failed."; exit 1; fi
expiry_date=$(date -d "$(curl -s "$data_acc$data_key")" +%s)
current_date=$(date +%s)
remaining_days=$(( (expiry_date - current_date) / 86400 ))
if [ "$expiry_date" -le "$current_date" ]; then echo "PERMISSION DENIED! Script access has expired."; exit 1; fi

action="$1"
shift # Remove the action argument

# --- Functions ---

restart_all_services() {
    echo "RESTARTING SERVER SERVICES..."
    services=(
        "ssh" "dropbear" "ws" "openvpn" "nginx" "haproxy"
        "xray@vmess" "xray@vless" "xray@trojan" "xray@shadowsocks"
        "dnstt-server" "dnstt-client"
    )
    local failed_services=()
    for service in "${services[@]}"; do
        systemctl restart "$service" >/dev/null 2>&1
        if [ $? -eq 0 ]; then
            echo "Service $service: OK"
        else
            echo "Service $service: FAILED"
            failed_services+=("$service")
        fi
    done
    if [ ${#failed_services[@]} -eq 0 ]; then
        echo "All services restart command issued successfully."
    else
        echo "Some services failed to restart: ${failed_services[*]}"
        exit 1 # Indicate partial failure
    fi
}

check_bandwidth_usage() {
    if ! command -v vnstat &>/dev/null; then
        echo "Error: vnstat is not installed. Please install it first."
        exit 1
    fi
    if [ -z "$(vnstat --iflist)" ]; then
        echo "Error: No network interfaces available for vnstat. Please ensure vnstat is configured."
        exit 1
    fi
    echo "--- BANDWIDTH USAGE ---"
    vnstat # Full vnstat output
}

get_port_information() {
    echo "--- SERVER PORT INFORMATION ---"
    echo "• OpenSSH          : 22, 443, 80"
    echo "• Dropbear         : 443, 109, 143"
    echo "• SSH Websocket    : 80, 443"
    echo "• OpenVPN          : 443, 1194, 2200"
    echo "• Nginx            : 80, 81, 443"
    echo "• Haproxy          : 80, 443"
    echo "• DNS              : 53, 443"
    echo "• XRAY Vmess       : 80, 443"
    echo "• XRAY Vless       : 80, 443"
    echo "• Trojan           : 443"
    echo "• Shadowsocks      : 443"
    
    TZ_INFO=$(cat /etc/timezone 2>/dev/null || echo "Unknown")
    if [[ -f /etc/cron.d/daily_reboot ]]; then
        reboot_time=$(grep -oP '^\d+\s+\d+' /etc/cron.d/daily_reboot | head -1 | awk '{printf "%02d:%02d", $2, $1}')
        echo "• Time Zone        : ${TZ_INFO}"
        echo "• Automatic Reboot : ${reboot_time} GMT +6"
    else
        echo "• Time Zone        : ${TZ_INFO}"
        echo "• Automatic Reboot : Not Set"
    fi
    echo "• Auto Delete Expired: Yes"
}

change_vps_domain() {
    local new_domain="$1"
    if [ -z "$new_domain" ]; then echo "Error: New domain cannot be empty."; exit 1; fi
    
    server_ip=$(wget -qO- ipv4.icanhazip.com 2>/dev/null || curl -s ipv4.icanhazip.com 2>/dev/null || echo "N/A")
    domain_ip=$(getent ahosts "$new_domain" | awk '{print $1}' | head -n 1)

    if [ "$server_ip" != "$domain_ip" ]; then
        echo "Error: Domain $new_domain does not resolve to server IP $server_ip. Aborting domain change."
        exit 1
    fi

    echo "$new_domain" > /etc/xray/domain
    
    echo "Attempting to renew SSL certificate with acme.sh..."
    # Ensure acme.sh is correctly installed and configured, typically in /root/.acme.sh
    if [ -d "/root/.acme.sh" ]; then
        /root/.acme.sh/acme.sh --upgrade --auto-upgrade >/dev/null 2>&1
        /root/.acme.sh/acme.sh --set-default-ca --server letsencrypt >/dev/null 2>&1
        /root/.acme.sh/acme.sh --issue -d "$new_domain" --standalone -k ec-256 >/dev/null 2>&1
        if [ $? -ne 0 ]; then
            echo "Warning: acme.sh certificate issuance failed for $new_domain. Check acme.sh logs (/root/.acme.sh/${new_domain}/) for details."
        else
            /root/.acme.sh/acme.sh --installcert -d "$new_domain" --fullchainpath /etc/xray/xray.crt --keypath /etc/xray/xray.key --ecc >/dev/null 2>&1
            # Ensure haproxy.pem is generated if used for SSL offloading
            if [ -f "/etc/xray/xray.crt" ] && [ -f "/etc/xray/xray.key" ]; then
                cat /etc/xray/xray.crt /etc/xray/xray.key | tee /etc/haproxy/yha.pem >/dev/null 2>&1
                chown www-data:www-data /etc/xray/xray.key /etc/xray/xray.crt >/dev/null 2>&1
            fi
        fi
    else
        echo "Warning: acme.sh not found in /root/.acme.sh. SSL certificate might not be updated."
    fi
    
    systemctl restart haproxy nginx >/dev/null 2>&1
    echo "Domain successfully changed to $new_domain."
    echo "It is highly recommended to reboot the VPS for all changes to apply completely."
}

change_vps_ns() {
    local new_ns="$1"
    if [ -z "$new_ns" ]; then echo "Error: Nameserver cannot be empty."; exit 1; fi
    
    local old_ns=$(cat /etc/xray/dns 2>/dev/null || echo "") 
    echo "$new_ns" >/etc/xray/dns

    if [ -f /etc/systemd/system/dnstt-client.service ]; then
        if [ -n "$old_ns" ]; then
            sed -i "s|$old_ns|$new_ns|g" /etc/systemd/system/dnstt-client.service
        fi
    fi
    if [ -f /etc/systemd/system/dnstt-server.service ]; then
        if [ -n "$old_ns" ]; then
            sed -i "s|$old_ns|$new_ns|g" /etc/systemd/system/dnstt-server.service
        fi
    fi
    
    systemctl daemon-reload >/dev/null 2>&1
    systemctl restart dnstt-server dnstt-client >/dev/null 2>&1
    echo "Nameserver successfully changed to $new_ns."
}

manage_auto_reboot_cron() {
    local action="$1"
    local reboot_hour="$2"

    case "$action" in
        set)
            if [[ ! "$reboot_hour" =~ ^(0[0-9]|1[0-9]|2[0-3])$ ]]; then
                echo "Error: Invalid hour. Please enter a two-digit hour from 00 to 23."
                exit 1
            fi
            echo "SHELL=/bin/sh" > /etc/cron.d/daily_reboot
            echo "PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin" >> /etc/cron.d/daily_reboot
            echo "0 $reboot_hour * * * root /sbin/reboot" >> /etc/cron.d/daily_reboot
            systemctl restart cron >/dev/null 2>&1
            echo "Auto reboot scheduled for $reboot_hour:00 daily."
            ;;
        disable)
            if [ -f /etc/cron.d/daily_reboot ]; then
                rm /etc/cron.d/daily_reboot
                systemctl restart cron >/dev/null 2>&1
                echo "Auto reboot disabled."
            else
                echo "Auto reboot is already disabled."
            fi
            ;;
        status)
            if [ -f /etc/cron.d/daily_reboot ]; then
                reboot_time=$(grep -oP '^\d+\s+\d+' /etc/cron.d/daily_reboot | head -1 | awk '{printf "%02d:%02d", $2, $1}')
                echo "Auto Reboot Status: ON (Scheduled at ${reboot_time} GMT +6 daily)"
            else
                echo "Auto Reboot Status: OFF"
            fi
            ;;
        *)
            echo "Error: Invalid action for auto reboot management."
            exit 1
            ;;
    esac
}

get_system_dashboard_info() {
    count_accounts() {
        if [ ! -e "/etc/xray/$1/.$1.db" ]; then
            mkdir -p "/etc/xray/$1"
            touch "/etc/xray/$1/.$1.db"
        fi
        accounts=$(cat "/etc/xray/$1/.$1.db" 2>/dev/null)
        if [[ $accounts = "" ]]; then
            echo "0"
        else
            cat "/etc/xray/$1/.$1.db" | grep "###" | wc -l
        fi
    }
    vm=$(count_accounts "vmess")
    vl=$(count_accounts "vless")
    tr=$(count_accounts "trojan")
    ss=$(count_accounts "shadowsocks")
    ssh=$(cat "/etc/ssh/.ssh.db" 2>/dev/null | grep "###" | wc -l || echo "0")

    get_service_status() {
        systemctl is-active --quiet "$1" && echo "Active" || echo "Inactive"
    }

    echo "--- SYSTEM DASHBOARD ---"
    echo "SYSTEM    : $(cat /etc/os-release 2>/dev/null | grep -w PRETTY_NAME | head -n1 | sed 's/=//g' | sed 's/"//g' | sed 's/PRETTY_NAME//g' | cut -d '.' -f 1-3 2>/dev/null || echo "N/A")"
    
    total_ram_kb=$(awk '/MemTotal/ {print $2}' /proc/meminfo 2>/dev/null || echo "N/A")
    available_ram_kb=$(awk '/MemAvailable/ {print $2}' /proc/meminfo 2>/dev/null || echo "N/A")

    if [ "$total_ram_kb" != "N/A" ] && [ "$available_ram_kb" != "N/A" ]; then
        total_ram_gb=$(awk "BEGIN {printf \"%.2f\", $total_ram_kb / 1024 / 1024}")
        used_ram_kb=$((total_ram_kb - available_ram_kb))
        used_ram_gb=$(awk "BEGIN {printf \"%.2f\", $used_ram_kb / 1024 / 1024}")
        echo "RAM       : ${total_ram_gb}GB / ${used_ram_gb}GB"
    else
        echo "RAM       : N/A"
    fi
    echo "UPTIME    : $(uptime -p 2>/dev/null | cut -d " " -f 2-10000 || echo "N/A")"
    echo "CPU CORE  : $(printf '%-1s' "$(grep -c cpu[0-9] /proc/stat 2>/dev/null || echo "N/A")")"
    echo "ISP       : $(cat /etc/xray/isp 2>/dev/null | cut -d ' ' -f 1-2 || echo "N/A")"
    echo "CITY      : $(cat /etc/xray/city 2>/dev/null || echo "N/A")"
    echo "IP        : $(wget -qO- ipv4.icanhazip.com 2>/dev/null || curl -s ipv4.icanhazip.com 2>/dev/null || echo "N/A")"
    echo "DOMAIN    : $(cat /etc/xray/domain 2>/dev/null || echo "No domain registered")"
    echo "NS        : $(cat /etc/xray/dns 2>/dev/null || echo "No NS registered")"
    echo "--- Account Counts ---"
    echo "SSH/OVPN    : $ssh ACCOUNT"
    echo "VMESS       : $vm ACCOUNT"
    echo "VLESS       : $vl ACCOUNT"
    echo "TROJAN      : $tr ACCOUNT"
    echo "SHADOWSOCKS : $ss ACCOUNT"
    echo "--- Service Status ---"
    echo "XRAY Vmess Service   : $(get_service_status xray@vmess)"
    echo "XRAY Vless Service   : $(get_service_status xray@vless)"
    echo "XRAY Trojan Service  : $(get_service_status xray@trojan)"
    echo "XRAY SSocks Service  : $(get_service_status xray@shadowsocks)"
    echo "Haproxy Service      : $(get_service_status haproxy)"
    echo "Nginx Service        : $(get_service_status nginx)"
    echo "SSH/OVPN Service     : $(get_service_status ssh)"

    SCRIPT_KEY=$(cat /root/.key 2>/dev/null || echo "N/A")
    echo "SCRIPT KEY : ${SCRIPT_KEY}"
    echo "SCRIPT EXP : $remaining_days DAYS REMAINING"
    echo "SCRIPT VERSION: V2.0 LTS"
}

# --- Main script logic: Call the function based on the first argument ---
case "$action" in
    restart_services)
        restart_all_services
        ;;
    check_bandwidth)
        check_bandwidth_usage
        ;;
    get_port_info)
        get_port_information
        ;;
    change_domain)
        change_vps_domain "$@"
        ;;
    change_ns)
        change_vps_ns "$@"
        ;;
    reboot_manage)
        manage_auto_reboot_cron "$@"
        ;;
    get_dashboard)
        get_system_dashboard_info
        ;;
    *)
        echo "Error: Unknown action or missing arguments for system settings."
        echo "Usage: system_actions.sh <action> [arguments]"
        echo "Actions: restart_services, check_bandwidth, get_port_info, change_domain <new_domain>, change_ns <new_ns>, reboot_manage <set <hour_24h>|disable|status>, get_dashboard"
        exit 1
        ;;
esac
exit 0
```

---

### ধাপ ৪: ব্যাশ স্ক্রিপ্টগুলোকে এক্সিকিউটেবল পারমিশন দিন

সবগুলো ফাইল সেভ করার পর, এই কমান্ডটি চালান:

```bash
sudo chmod +x /opt/sensi_bot_scripts/*.sh
```

---

### ধাপ ৫: পাইথন টেলিগ্রাম বট কোড (`bot.py`)

এটি `/root/telegram_bot/` ডিরেক্টরিতে থাকবে।

```python
import logging
import subprocess
import json
import re
from functools import wraps

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# --- Configuration ---
# IMPORTANT: Your Bot Token and Admin IDs
BOT_TOKEN = "7855565302:AAE9QUDuufs6SrE_vCHkhOOCUsdemr8hqUc" # User provided token
# This list will be updated dynamically for addadmin, but initial admins are here
ALLOWED_USER_IDS = [5487394544, 5967798239, 1956820398] # User provided IDs

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Helper function to escape MarkdownV2 special characters ---
def escape_markdown_v2(text: str) -> str:
    """Escapes characters that have special meaning in MarkdownV2."""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    # Escape backslash first, then other special characters.
    text = text.replace('\\', '\\\\')
    return re.sub(r'([%s])' % re.escape(escape_chars), r'\\\1', text)

# --- Authorization decorator ---
def authorized_only(func):
    """
    Decorator to ensure only allowed users can execute a command or callback.
    It's used for entry points of handlers.
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in ALLOWED_USER_IDS:
            logger.warning(f"Unauthorized access attempt by user ID: {user_id} trying to call {func.__name__}")
            
            if update.callback_query:
                await update.callback_query.answer("আপনি এই বটটি ব্যবহার করার জন্য অনুমোদিত নন।", show_alert=True)
                await update.callback_query.message.reply_text(
                    "আপনি এই বটটি ব্যবহার করার জন্য অনুমোদিত নন। অনুগ্রহ করে অ্যাডমিনের সাথে যোগাযোগ করুন।"
                )
            elif update.message:
                await update.message.reply_text(
                    "আপনি এই বটটি ব্যবহার করার জন্য অনুমোদিত নন। অনুগ্রহ করে অ্যাডমিনের সাথে যোগাযোগ করুন।"
                )
            return ConversationHandler.END # Stop conversation flow for unauthorized users
        
        # If authorized and it's a callback query, acknowledge it BEFORE proceeding
        if update.callback_query:
            await update.callback_query.answer()

        return await func(update, context)
    return wrapper

# --- Helper function to run bash scripts and handle output ---
async def run_bash_script(script_path, args, update: Update, parse_json=False):
    """Executes a bash script and sends its output/errors to the user."""
    message_obj = update.callback_query.message if update.callback_query else update.message

    sent_message = await message_obj.reply_text("কমান্ড কার্যকর করা হচ্ছে, অনুগ্রহ করে অপেক্ষা করুন...")
    
    try:
        command = [script_path] + [str(arg) for arg in args]
        logger.info(f"Executing: {command}")
        
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=300
        )
        
        output = process.stdout.strip()
        error_output = process.stderr.strip()

        await sent_message.edit_text("প্রক্রিয়া সম্পন্ন হয়েছে। ফলাফল:")

        if process.returncode != 0:
            full_error_message = f"❌ *কমান্ড এক্সিকিউশন ব্যর্থ হয়েছে, এক্সিট কোড `{process.returncode}`*\n"
            if output:
                full_error_message += f"স্ট্যান্ডার্ড আউটপুট:\n```\n{escape_markdown_v2(output)}\n```\n"
            if error_output:
                full_error_message += f"ত্রুটি আউটপুট:\n```\n{escape_markdown_v2(error_output)}\n```"
            
            if len(full_error_message) > 4000:
                full_error_message = full_error_message[:3900] + "\n... (আউটপুট সংক্ষিপ্ত)"
            
            await message_obj.reply_text(f"{full_error_message}", parse_mode="MarkdownV2")
            logger.error(f"Script {script_path} failed: {full_error_message}")
            return None

        if parse_json:
            try:
                json_match = re.search(r'\{.*\}', output, re.DOTALL)
                if json_match:
                    json_data = json.loads(json_match.group(0))
                    if json_data.get("status") == "error":
                        error_message_from_script = json_data.get("detail", json_data.get("message", "অজানা ত্রুটি"))
                        await message_obj.reply_text(f"❌ *স্ক্রিপ্ট থেকে ত্রুটি:*\n{escape_markdown_v2(error_message_from_script)}", parse_mode="MarkdownV2")
                        return None
                    return json_data
                else:
                    await message_obj.reply_text(
                        f"✅ কমান্ড সফল হয়েছে, কিন্তু JSON আউটপুট খুঁজে পাওয়া যায়নি বা ভুল ছিল। কাঁচা আউটপুট:\n```\n{escape_markdown_v2(output)}\n```",
                        parse_mode="MarkdownV2"
                    )
                    logger.warning(f"Script {script_path} did not return valid JSON: {output}")
                    return None
            except json.JSONDecodeError as e:
                await message_obj.reply_text(
                    f"❌ স্ক্রিপ্ট আউটপুট থেকে JSON পার্স করতে ব্যর্থ: {e}\nকাঁচা আউটপুট:\n```\n{escape_markdown_v2(output)}\n```",
                    parse_mode="MarkdownV2"
                )
                logger.error(f"JSON decoding error from {script_path}: {e} - Raw output: {output}")
                return None
        else:
            if output:
                formatted_output = escape_markdown_v2(output)
                
                if len(formatted_output) > 4000:
                    formatted_output = formatted_output[:3900] + "\n... (আউটপুট সংক্ষিপ্ত)"
                
                await message_obj.reply_text(f"```\n{formatted_output}\n```", parse_mode="MarkdownV2")
            else:
                await message_obj.reply_text("✅ কমান্ড সফল হয়েছে, কিন্তু কোনো আউটপুট ফেরত আসেনি।")
            return True

    except FileNotFoundError:
        await message_obj.reply_text("❌ *ত্রুটি:* সার্ভারে স্ক্রিপ্ট খুঁজে পাওয়া যায়নি। পথ এবং পারমিশন চেক করুন।")
        logger.error(f"Script not found at {script_path}. Check path and permissions.")
        return None
    except subprocess.TimeoutExpired:
        await message_obj.reply_text("❌ *ত্রুটি:* কমান্ড সময়সীমা অতিক্রম করেছে।")
        logger.error(f"Script {script_path} timed out.")
        return None
    except Exception as e:
        await message_obj.reply_text(f"❌ *একটি অপ্রত্যাশিত অভ্যন্তরীণ ত্রুটি ঘটেছে:* {e}")
        logger.critical(f"An unexpected error occurred while running {script_path}: {e}")
        return None

# --- Main Menu (Command) ---
@authorized_only
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text_raw = (
        "স্বাগতম! এই বটটি আপনার VPS অ্যাকাউন্ট দূর থেকে ম্যানেজ করতে সাহায্য করে।\n\n"
        "*প্রধান কমান্ডসমূহ:*\n"
        "  - `/help`: এই সাহায্য বার্তাটি দেখান।\n"
        "  - `/add <প্রোটোকল> <ইউজারনেম> <পাসওয়ার্ড_যদি_থাকে> <দিন> <কোটা_জিবি> <আইপি_লিমিট>`: নতুন অ্যাকাউন্ট তৈরি করুন।\n"
        "      _উদাহরণ: `/add ssh user1 pass123 30 0 1`_\n"
        "      _উদাহরণ: `/add vmess user2 dummy_pass 60 100 2`_ (Xray এর জন্য পাসওয়ার্ড ব্যবহৃত হয় না, কিন্তু একটি দিতে হয়)\n"
        "  - `/del <প্রোটোকল> <ইউজারনেম>`: অ্যাকাউন্ট মুছুন।\n"
        "      _উদাহরণ: `/del ssh user1`_\n"
        "  - `/renew <প্রোটোকল> <ইউজারনেম> <অতিরিক্ত_দিন> <নতুন_কোটা_জিবি> <নতুন_আইপি_লিমিট>`: অ্যাকাউন্ট রিনিউ করুন।\n"
        "      _উদাহরণ: `/renew vmess user2 30 150 2`_\n"
        "  - `/trial <প্রোটোকল> <মিনিট>`: ট্রায়াল অ্যাকাউন্ট তৈরি করুন।\n"
        "      _উদাহরণ: `/trial ssh 60`_\n"
        "  - `/check <প্রোটোকল>`: অ্যাকাউন্টের সক্রিয় সংযোগ এবং ব্যবহারের তথ্য দেখুন।\n"
        "      _উদাহরণ: `/check vmess`_\n\n"
        "*সিস্টেম ম্যানেজমেন্ট কমান্ডসমূহ:*\n"
        "  - `/dashboard`: সিস্টেমের বর্তমান অবস্থা, RAM, CPU, অ্যাকাউন্ট গণনা ইত্যাদি দেখুন।\n"
        "  - `/restart_services`: SSH, OpenVPN, Xray, Nginx, Haproxy সহ সকল সার্ভিস রিস্টার্ট করুন।\n"
        "  - `/check_bandwidth`: `vnstat` ব্যবহার করে ব্যান্ডউইথের ব্যবহার দেখুন।\n"
        "  - `/show_ports`: সার্ভিসের পোর্ট এবং অন্যান্য সেটিং-এর তথ্য দেখুন।\n"
        "  - `/change_domain <নতুন_ডোমেইন>`: আপনার VPS-এর ডোমেইন পরিবর্তন করুন।\n"
        "      _উদাহরণ: `/change_domain mynewdomain.com`_\n"
        "  - `/change_ns <নতুন_নেমসার্ভার>`: DNS (Nameserver) পরিবর্তন করুন।\n"
        "      _উদাহরণ: `/change_ns ns.mynewdns.com`_\n"
        "  - `/reboot_set <ঘণ্টা_২৪ঘণ্টা_ফরম্যাট>`: সার্ভার অটো রিবুট সেট করুন।\n"
        "      _উদাহরণ: `/reboot_set 03` (রাত ৩টা) বা `/reboot_set 14` (দুপুর ২টা)_\n"
        "  - `/reboot_disable`: অটো রিবুট ডিজেবল করুন।\n"
        "  - `/reboot_status`: অটো রিবুট স্ট্যাটাস দেখুন।\n\n"
        "*অ্যাডমিন ম্যানেজমেন্ট (শুধুমাত্র প্রধান অ্যাডমিন):*\n"
        "  - `/addadmin <user_id>`: নতুন অ্যাডমিন যোগ করুন।\n"
        "  - `/removeadmin <user_id>`: অ্যাডমিন সরান।\n"
        "  - `/listadmins`: সকল অ্যাডমিন আইডি দেখুন।"
    )
    escaped_help_text = escape_markdown_v2(help_text_raw)
    await update.message.reply_text(escaped_help_text, parse_mode="MarkdownV2")

# --- Help Command ---
@authorized_only
async def help_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await start_command(update, context) # /help will show the same message as /start


# --- Account Management Commands ---
@authorized_only
async def add_account_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    # <protocol> <username> <password_or_dummy> <duration_days> <quota_gb> <ip_limit>
    if len(args) != 6:
        await update.message.reply_text(
            "❌ ভুল ব্যবহার। ব্যবহার: `/add <প্রোটোকল> <ইউজারনেম> <পাসওয়ার্ড_যদি_থাকে> <দিন> <কোটা_জিবি> <আইপি_লিমিট>`\n"
            "উদাহরণ: `/add ssh user1 pass123 30 0 1`\n"
            "উদাহরণ: `/add vmess user2 dummy_pass 60 100 2` (Xray এর জন্য পাসওয়ার্ড ব্যবহৃত হয় না, কিন্তু একটি দিতে হয়)\n",
            parse_mode="MarkdownV2"
        )
        return

    protocol, username, password, duration_days, quota_gb, ip_limit = args
    
    # Basic validation (can be more robust if needed)
    if not duration_days.isdigit() or int(duration_days) <= 0:
        await update.message.reply_text("❌ 'দিন' অবশ্যই একটি ধনাত্মক সংখ্যা হতে হবে।")
        return
    if not quota_gb.isdigit() or int(quota_gb) < 0:
        await update.message.reply_text("❌ 'কোটা জিবি' অবশ্যই একটি অঋণাত্মক সংখ্যা হতে হবে।")
        return
    if not ip_limit.isdigit() or int(ip_limit) < 0:
        await update.message.reply_text("❌ 'আইপি লিমিট' অবশ্যই একটি অঋণাত্মক সংখ্যা হতে হবে।")
        return

    result = await run_bash_script("/opt/sensi_bot_scripts/create_account.sh", 
                                   [protocol, username, password, duration_days, quota_gb, ip_limit], 
                                   update, parse_json=True)

    if result and result.get("status") == "success":
        data = result.get("data", {})
        response_message = f"✅ *অ্যাকাউন্ট সফলভাবে তৈরি হয়েছে:*\n\n"
        for key, value in data.items():
            # Customize display of certain fields or add specific links
            if key in ["status", "message"]: continue
            if key.endswith("_link") or key.endswith("_payload"): continue # Handle links separately
            
            response_message += f"  `{escape_markdown_v2(key.replace('_', ' ').title())}`: `{escape_markdown_v2(str(value))}`\n"
        
        # Specific link display based on protocol
        if protocol == "vmess":
            response_message += f"\n*VMess লিঙ্ক:*\n" \
                                f"  TLS: `{escape_markdown_v2(data.get('vmess_tls_link', 'N/A'))}`\n" \
                                f"  Non-TLS: `{escape_markdown_v2(data.get('vmess_nontls_link', 'N/A'))}`\n" \
                                f"  gRPC: `{escape_markdown_v2(data.get('vmess_grpc_link', 'N/A'))}`\n"
        elif protocol == "vless":
            response_message += f"\n*VLESS লিঙ্ক:*\n" \
                                f"  TLS: `{escape_markdown_v2(data.get('vless_tls_link', 'N/A'))}`\n" \
                                f"  Non-TLS: `{escape_markdown_v2(data.get('vless_nontls_link', 'N/A'))}`\n" \
                                f"  gRPC: `{escape_markdown_v2(data.get('vless_grpc_link', 'N/A'))}`\n"
        elif protocol == "trojan":
            response_message += f"\n*TROJAN লিঙ্ক:*\n" \
                                f"  TLS: `{escape_markdown_v2(data.get('trojan_tls_link', 'N/A'))}`\n" \
                                f"  gRPC: `{escape_markdown_v2(data.get('trojan_grpc_link', 'N/A'))}`\n"
        elif protocol == "shadowsocks":
            response_message += f"\n*SHADOWSOCKS লিঙ্ক:*\n" \
                                f"  WS: `{escape_markdown_v2(data.get('ss_link_ws', 'N/A'))}`\n" \
                                f"  gRPC: `{escape_markdown_v2(data.get('ss_link_grpc', 'N/A'))}`\n"
        elif protocol == "ssh":
            response_message += f"\n*SSH/OVPN বিস্তারিত:*\n" \
                                f"  পাসওয়ার্ড: `{escape_markdown_v2(data.get('password', 'N/A'))}`\n" \
                                f"  OpenVPN লিঙ্ক: `{escape_markdown_v2(data.get('openvpn_link', 'N/A'))}`\n" \
                                f"  অ্যাকাউন্ট সেভ লিঙ্ক: `{escape_markdown_v2(data.get('save_account_link', 'N/A'))}`\n"
        
        await update.message.reply_text(response_message, parse_mode="MarkdownV2")
    else:
        await update.message.reply_text("❌ অ্যাকাউন্ট তৈরি করতে ব্যর্থ হয়েছে। অনুগ্রহ করে স্ক্রিপ্ট আউটপুট চেক করুন।")

@authorized_only
async def delete_account_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) != 2:
        await update.message.reply_text("❌ ভুল ব্যবহার। ব্যবহার: `/del <প্রোটোকল> <ইউজারনেম>`\nউদাহরণ: `/del ssh user1`", parse_mode="MarkdownV2")
        return
    
    protocol, username = args
    result = await run_bash_script("/opt/sensi_bot_scripts/delete_account.sh", [protocol, username], update, parse_json=True)

    if result and result.get("status") == "success":
        await update.message.reply_text(f"✅ অ্যাকাউন্ট `{escape_markdown_v2(protocol)}`: `{escape_markdown_v2(username)}` সফলভাবে মুছে ফেলা হয়েছে।", parse_mode="MarkdownV2")
    else:
        await update.message.reply_text("❌ অ্যাকাউন্ট মুছতে ব্যর্থ হয়েছে। অনুগ্রহ করে স্ক্রিপ্ট আউটপুট চেক করুন।")

@authorized_only
async def renew_account_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    # <protocol> <username> <add_days> <new_quota_gb> <new_ip_limit>
    if len(args) != 5:
        await update.message.reply_text(
            "❌ ভুল ব্যবহার। ব্যবহার: `/renew <প্রোটোকল> <ইউজারনেম> <অতিরিক্ত_দিন> <নতুন_কোটা_জিবি> <নতুন_আইপি_লিমিট>`\n"
            "উদাহরণ: `/renew vmess user2 30 150 2`",
            parse_mode="MarkdownV2"
        )
        return
    
    protocol, username, add_days, new_quota_gb, new_ip_limit = args

    if not add_days.isdigit() or int(add_days) <= 0:
        await update.message.reply_text("❌ 'অতিরিক্ত দিন' অবশ্যই একটি ধনাত্মক সংখ্যা হতে হবে।")
        return
    if not new_quota_gb.isdigit() or int(new_quota_gb) < 0:
        await update.message.reply_text("❌ 'নতুন কোটা জিবি' অবশ্যই একটি অঋণাত্মক সংখ্যা হতে হবে।")
        return
    if not new_ip_limit.isdigit() or int(new_ip_limit) < 0:
        await update.message.reply_text("❌ 'নতুন আইপি লিমিট' অবশ্যই একটি অঋণাত্মক সংখ্যা হতে হবে।")
        return

    result = await run_bash_script("/opt/sensi_bot_scripts/renew_account.sh", 
                                   [protocol, username, add_days, new_quota_gb, new_ip_limit], 
                                   update, parse_json=True)

    if result and result.get("status") == "success":
        data = result.get("data", {})
        response_message = f"✅ অ্যাকাউন্ট `{escape_markdown_v2(protocol)}`: `{escape_markdown_v2(data.get('username'))}` সফলভাবে রিনিউ করা হয়েছে।\n" \
                           f"নতুন মেয়াদ: `{escape_markdown_v2(data.get('exp', 'N/A'))}`\n" \
                           f"নতুন কোটা: `{escape_markdown_v2(str(data.get('quota', 'N/A')))}`\n" \
                           f"নতুন IP সীমা: `{escape_markdown_v2(str(data.get('limitip', 'N/A')))}`"
        await update.message.reply_text(response_message, parse_mode="MarkdownV2")
    else:
        await update.message.reply_text("❌ অ্যাকাউন্ট রিনিউ করতে ব্যর্থ হয়েছে। অনুগ্রহ করে স্ক্রিপ্ট আউটপুট চেক করুন।")

@authorized_only
async def trial_account_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) != 2:
        await update.message.reply_text("❌ ভুল ব্যবহার। ব্যবহার: `/trial <প্রোটোকল> <মিনিট>`\nউদাহরণ: `/trial ssh 60`", parse_mode="MarkdownV2")
        return
    
    protocol, duration_minutes = args

    if not duration_minutes.isdigit() or int(duration_minutes) <= 0:
        await update.message.reply_text("❌ 'মিনিট' অবশ্যই একটি ধনাত্মক সংখ্যা হতে হবে।")
        return
    
    result = await run_bash_script("/opt/sensi_bot_scripts/create_trial_account.sh", 
                                   [protocol, duration_minutes], 
                                   update, parse_json=True)

    if result and result.get("status") == "success":
        data = result.get("data", {})
        response_message = f"✅ *ট্রায়াল অ্যাকাউন্ট সফলভাবে তৈরি হয়েছে:*\n\n"
        for key, value in data.items():
            if key in ["status", "message"]: continue
            if key.endswith("_link"): continue # Handle links separately
            response_message += f"  `{escape_markdown_v2(key.replace('_', ' ').title())}`: `{escape_markdown_v2(str(value))}`\n"
        
        if protocol == "vmess":
            response_message += f"\n*VMess লিঙ্ক:*\n" \
                                f"  TLS: `{escape_markdown_v2(data.get('vmess_tls_link', 'N/A'))}`\n" \
                                f"  Non-TLS: `{escape_markdown_v2(data.get('vmess_nontls_link', 'N/A'))}`\n"
        # Add other trial protocol links here (vless, trojan, ss)
        
        await update.message.reply_text(response_message, parse_mode="MarkdownV2")
    else:
        await update.message.reply_text("❌ ট্রায়াল অ্যাকাউন্ট তৈরি করতে ব্যর্থ হয়েছে। অনুগ্রহ করে স্ক্রিপ্ট আউটপুট চেক করুন।")

@authorized_only
async def check_account_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) != 1:
        await update.message.reply_text("❌ ভুল ব্যবহার। ব্যবহার: `/check <প্রোটোকল>`\nউদাহরণ: `/check vmess`", parse_mode="MarkdownV2")
        return
    
    protocol = args[0]
    result = await run_bash_script("/opt/sensi_bot_scripts/check_account.sh", [protocol], update, parse_json=True)

    if result and result.get("status") == "success":
        data = result.get("data", [])
        if not data:
            await update.message.reply_text(f"এই মুহূর্তে `{escape_markdown_v2(protocol)}` অ্যাকাউন্টের জন্য কোনো সক্রিয় সংযোগ নেই।", parse_mode="MarkdownV2")
            return

        response_message = f"📊 *`{escape_markdown_v2(protocol.upper())}` অ্যাকাউন্টের সক্রিয় সংযোগ:*\n\n"
        for entry in data:
            response_message += f"👤 *ব্যবহারকারী:* `{escape_markdown_v2(entry.get('user', 'N/A'))}`\n"
            response_message += f"  ব্যবহার: `{escape_markdown_v2(str(entry.get('usage', 'N/A')))}`\n"
            response_message += f"  কোটা: `{escape_markdown_v2(str(entry.get('quota', 'N/A')))}`\n"
            response_message += f"  IP সীমা: `{escape_markdown_v2(str(entry.get('ip_limit', 'N/A')))}`\n"
            response_message += f"  IP গণনা: `{escape_markdown_v2(str(entry.get('ip_count', 'N/A')))}`\n"
            response_message += f"  মেয়াদ: `{escape_markdown_v2(entry.get('expiration', 'N/A'))}`\n\n"
        
        if len(response_message) > 4000:
            response_message = response_message[:3900] + "\n... (আউটপুট সংক্ষিপ্ত)"
        
        await update.message.reply_text(response_message, parse_mode="MarkdownV2")
    else:
        await update.message.reply_text("❌ অ্যাকাউন্ট চেক করতে ব্যর্থ হয়েছে। অনুগ্রহ করে স্ক্রিপ্ট আউটপুট চেক করুন।")

# --- System Management Commands ---
@authorized_only
async def dashboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await run_bash_script("/opt/sensi_bot_scripts/system_actions.sh", ["get_dashboard"], update, parse_json=False)

@authorized_only
async def restart_services_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await run_bash_script("/opt/sensi_bot_scripts/system_actions.sh", ["restart_services"], update, parse_json=False)

@authorized_only
async def check_bandwidth_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await run_bash_script("/opt/sensi_bot_scripts/system_actions.sh", ["check_bandwidth"], update, parse_json=False)

@authorized_only
async def show_ports_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await run_bash_script("/opt/sensi_bot_scripts/system_actions.sh", ["get_port_info"], update, parse_json=False)

@authorized_only
async def change_domain_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) != 1:
        await update.message.reply_text("❌ ভুল ব্যবহার। ব্যবহার: `/change_domain <নতুন_ডোমেইন>`\nউদাহরণ: `/change_domain mynewdomain.com`", parse_mode="MarkdownV2")
        return
    new_domain = args[0]
    await run_bash_script("/opt/sensi_bot_scripts/system_actions.sh", ["change_domain", new_domain], update, parse_json=False)

@authorized_only
async def change_ns_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) != 1:
        await update.message.reply_text("❌ ভুল ব্যবহার। ব্যবহার: `/change_ns <নতুন_নেমসার্ভার>`\nউদাহরণ: `/change_ns ns.mynewdns.com`", parse_mode="MarkdownV2")
        return
    new_ns = args[0]
    await run_bash_script("/opt/sensi_bot_scripts/system_actions.sh", ["change_ns", new_ns], update, parse_json=False)

@authorized_only
async def reboot_set_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) != 1 or not args[0].isdigit() or not (0 <= int(args[0]) <= 23):
        await update.message.reply_text("❌ ভুল ব্যবহার। ব্যবহার: `/reboot_set <ঘণ্টা_২৪ঘণ্টা_ফরম্যাট>`\nউদাহরণ: `/reboot_set 03` (রাত ৩টা)", parse_mode="MarkdownV2")
        return
    reboot_hour = args[0]
    await run_bash_script("/opt/sensi_bot_scripts/system_actions.sh", ["reboot_manage", "set", reboot_hour], update, parse_json=False)

@authorized_only
async def reboot_disable_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await run_bash_script("/opt/sensi_bot_scripts/system_actions.sh", ["reboot_manage", "disable"], update, parse_json=False)

@authorized_only
async def reboot_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await run_bash_script("/opt/sensi_bot_scripts/system_actions.sh", ["reboot_manage", "status"], update, parse_json=False)

# --- Admin Management Commands ---
@authorized_only
async def add_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Only the first admin (super admin) can add/remove other admins
    if update.effective_user.id != ALLOWED_USER_IDS[0]:
        await update.message.reply_text("❌ শুধুমাত্র প্রধান অ্যাডমিন নতুন অ্যাডমিন যোগ করতে পারেন।")
        return

    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text("ব্যবহার: `/addadmin <user_id>` (ইউজার আইডি একটি সংখ্যা হতে হবে)", parse_mode="MarkdownV2")
        return

    new_admin_id = int(args[0])
    if new_admin_id in ALLOWED_USER_IDS:
        await update.message.reply_text(f"ব্যবহারকারী `{new_admin_id}` ইতিমধ্যেই অ্যাডমিন।", parse_mode="MarkdownV2")
        return

    ALLOWED_USER_IDS.append(new_admin_id)
    await update.message.reply_text(f"✅ ব্যবহারকারী `{new_admin_id}` কে সফলভাবে অ্যাডমিন হিসেবে যোগ করা হয়েছে।", parse_mode="MarkdownV2")
    logger.info(f"User {new_admin_id} added as admin by {update.effective_user.id}. Current admins: {ALLOWED_USER_IDS}")

@authorized_only
async def remove_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Only the first admin (super admin) can add/remove other admins
    if update.effective_user.id != ALLOWED_USER_IDS[0]:
        await update.message.reply_text("❌ শুধুমাত্র প্রধান অ্যাডমিন অ্যাডমিন সরাতে পারেন।")
        return

    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text("ব্যবহার: `/removeadmin <user_id>` (ইউজার আইডি একটি সংখ্যা হতে হবে)", parse_mode="MarkdownV2")
        return

    admin_to_remove_id = int(args[0])
    if admin_to_remove_id == ALLOWED_USER_IDS[0]:
        await update.message.reply_text("❌ আপনি প্রধান অ্যাডমিনকে সরাতে পারবেন না।")
        return
    
    if admin_to_remove_id not in ALLOWED_USER_IDS:
        await update.message.reply_text(f"ব্যবহারকারী `{admin_to_remove_id}` অ্যাডমিন নয়।", parse_mode="MarkdownV2")
        return

    ALLOWED_USER_IDS.remove(admin_to_remove_id)
    await update.message.reply_text(f"✅ ব্যবহারকারী `{admin_to_remove_id}` কে সফলভাবে অ্যাডমিন থেকে সরানো হয়েছে।", parse_mode="MarkdownV2")
    logger.info(f"User {admin_to_remove_id} removed from admins by {update.effective_user.id}. Current admins: {ALLOWED_USER_IDS}")

@authorized_only
async def list_admins_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    admin_list_str = "\n".join([f"- `{uid}`" for uid in ALLOWED_USER_IDS])
    await update.message.reply_text(f"*বর্তমান অ্যাডমিনরা:*\n{admin_list_str}", parse_mode="MarkdownV2")

# --- Fallback for unknown commands/messages ---
async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("দুঃখিত, আমি এই কমান্ডটি বুঝতে পারছি না। উপলব্ধ কমান্ডগুলির জন্য `/help` টাইপ করুন।")

async def unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # For any non-command text messages
    await update.message.reply_text("দুঃখিত, আমি এই মেসেজটি বুঝতে পারছি না। উপলব্ধ কমান্ডগুলির জন্য `/help` টাইপ করুন।")


def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    # --- Register Command Handlers (all authorized_only) ---
    application.add_handler(CommandHandler("start", authorized_only(start_command)))
    application.add_handler(CommandHandler("help", authorized_only(help_command_handler)))

    # Account Management Commands
    application.add_handler(CommandHandler("add", authorized_only(add_account_command)))
    application.add_handler(CommandHandler("del", authorized_only(delete_account_command)))
    application.add_handler(CommandHandler("renew", authorized_only(renew_account_command)))
    application.add_handler(CommandHandler("trial", authorized_only(trial_account_command)))
    application.add_handler(CommandHandler("check", authorized_only(check_account_command)))

    # System Management Commands
    application.add_handler(CommandHandler("dashboard", authorized_only(dashboard_command)))
    application.add_handler(CommandHandler("restart_services", authorized_only(restart_services_command)))
    application.add_handler(CommandHandler("check_bandwidth", authorized_only(check_bandwidth_command)))
    application.add_handler(CommandHandler("show_ports", authorized_only(show_ports_command)))
    application.add_handler(CommandHandler("change_domain", authorized_only(change_domain_command)))
    application.add_handler(CommandHandler("change_ns", authorized_only(change_ns_command)))
    application.add_handler(CommandHandler("reboot_set", authorized_only(reboot_set_command)))
    application.add_handler(CommandHandler("reboot_disable", authorized_only(reboot_disable_command)))
    application.add_handler(CommandHandler("reboot_status", authorized_only(reboot_status_command)))

    # Admin Management Commands
    application.add_handler(CommandHandler("addadmin", authorized_only(add_admin_command)))
    application.add_handler(CommandHandler("removeadmin", authorized_only(remove_admin_command)))
    application.add_handler(CommandHandler("listadmins", authorized_only(list_admins_command)))

    # Fallback handlers for unknown commands/messages (should be after all specific handlers)
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_message))
    
    # Handle CallbackQueryHandlers if any are accidentally left (e.g., old messages with buttons)
    # This will direct any unexpected callback query to the unknown_command handler.
    application.add_handler(CallbackQueryHandler(authorized_only(unknown_command)))


    logger.info("বট চালু হচ্ছে...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()```

---

### ধাপ ৬: পাইথন বট ফাইল সেভ করুন এবং পারমিশন দিন

1.  উপরে দেওয়া পাইথন কোডটি কপি করুন।
2.  আপনার সার্ভারে `/root/telegram_bot/bot.py` ফাইলটি খুলুন:
    ```bash
    sudo nano /root/telegram_bot/bot.py
    ```
3.  ফাইলের সম্পূর্ণ কন্টেন্ট মুছে ফেলুন এবং নতুন কোড পেস্ট করুন।
4.  সেভ করুন (Ctrl+O, Enter, Ctrl+X)।

---

### ধাপ ৭: `systemd` সার্ভিস ফাইল আপডেট করুন

যদি আপনার `mybot.service` ফাইলটি এখনও বিদ্যমান থাকে, তাহলে এটি খুলুন এবং নিশ্চিত করুন যে এটি সঠিক path নির্দেশ করছে:

```bash
sudo nano /etc/systemd/system/mybot.service
```

নিচের কন্টেন্টটি নিশ্চিত করুন:

```ini
[Unit]
Description=Sensi-Tunnel Telegram Bot
After=network.target

[Service]
User=root
WorkingDirectory=/root/telegram_bot/
ExecStart=/usr/bin/python3 /root/telegram_bot/bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

সেভ করুন (Ctrl+O, Enter, Ctrl+X)।

---

### ধাপ ৮: সার্ভিস রিলোড এবং স্টার্ট করুন

1.  systemd ডেমন রিলোড করুন:
    ```bash
    sudo systemctl daemon-reload
    ```2.  বট সার্ভিস স্টার্ট করুন:
    ```bash
    sudo systemctl start mybot.service
    ```
3.  লগগুলো চেক করুন:
    ```bash
    sudo journalctl -u mybot.service -f
    ```

এখন বটটি সম্পূর্ণরূপে নতুন লজিক ব্যবহার করে কাজ করবে। Xray কনফিগারেশন লজিক পূরণ করার পরে, অ্যাকাউন্ট ম্যানেজমেন্ট ফাংশনগুলো সঠিকভাবে কাজ করা উচিত।
