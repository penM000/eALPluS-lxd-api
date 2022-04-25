# セットアップ方法

## 実行環境の構築

### lxd インストール
lxdのインストールを行います。
インストールには、snapを用いて行います。
```bash
sudo snap install lxd
# もしくは
sudo snap refresh lxd
```

### lxd の初期設定
```bash 
sudo usermod -aG lxd $USER
sudo lxd init
# 以下出力
Would you like to use LXD clustering? (yes/no) [default=no]: no
Do you want to configure a new storage pool? (yes/no) [default=yes]: yes
Name of the new storage pool [default=default]: default
Name of the storage backend to use (lvm, zfs, ceph, btrfs, dir) [default=zfs]: zfs
Create a new ZFS pool? (yes/no) [default=yes]: yes
Would you like to use an existing empty block device (e.g. a disk or partition)? (yes/no) [default=no]: no
Size in GB of the new loop device (1GB minimum) [default=30GB]: 128GB
Would you like to connect to a MAAS server? (yes/no) [default=no]: no
Would you like to create a new local network bridge? (yes/no) [default=yes]: yes
What should the new bridge be called? [default=lxdbr0]: lxdbr0
What IPv4 address should be used? (CIDR subnet notation, “auto” or “none”) [default=auto]: auto
What IPv6 address should be used? (CIDR subnet notation, “auto” or “none”) [default=auto]: auto
Would you like the LXD server to be available over the network? (yes/no) [default=no]: no
Would you like stale cached images to be updated automatically? (yes/no) [default=yes] yes
Would you like a YAML "lxd init" preseed to be printed? (yes/no) [default=no]: yes
```
```yml
config: {}
networks:
- config:
    ipv4.address: auto
    ipv6.address: auto
  description: ""
  name: lxdbr0
  type: ""
  project: default
storage_pools:
- config:
    size: 128GB
  description: ""
  name: default
  driver: zfs
profiles:
- config: {}
  description: ""
  devices:
    eth0:
      name: eth0
      network: lxdbr0
      type: nic
    root:
      path: /
      pool: default
      type: disk
  name: default
projects: []
cluster: null
```

初期設定が終わったら、正しく動作するかを確認します。
```bash
lxc list

+------+-------+------+------+------+-----------+
| NAME | STATE | IPV4 | IPV6 | TYPE | SNAPSHOTS |
+------+-------+------+------+------+-----------+
# 下記のようなエラーが出る場合は、再度ログインを行ってください。
Error: Get "http://unix.socket/1.0": dial unix /var/snap/lxd/common/lxd/unix.socket: connect: permission denied

```
下記のコマンドでコンテナを作成します。
```bash
lxc launch ubuntu test

Creating test
The local image 'ubuntu' couldn't be found, trying 'ubuntu:' instead.
Retrieving image: rootfs: 38% (729.97kB/s)
Starting test

```
