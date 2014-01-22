# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
        # Base box to build off, and download URL for when it doesn't exist
        # on the user's system already
        ubuntu_release = "raring"
        ip_address = "192.168.79.2"

        config.vm.box = "#{ubuntu_release}-server64"
        config.vm.box_url =
"http://cloud-images.ubuntu.com/vagrant/#{ubuntu_release}/current/#{ubuntu_release}-server-cloudimg-amd64-vagrant-disk1.box"

        config.vm.hostname = "openahjodev.localdomain"

        # Assign this VM to a host only network IP, allowing you to access
        # it
        # via the IP.
        config.vm.network "private_network", ip: ip_address
        #config.ssh.host = ip_address
        #config.ssh.port = 22

        # Forward a port from the guest to the host, which allows for
        # outside
        # computers to access the VM, whereas host only networking does not.
        config.vm.network "forwarded_port", guest: 8000, host: 8079
        config.vm.network "forwarded_port", guest: 22, host: 2279, id: "ssh", auto_correct: true

        config.vm.provider "virtualbox" do |v|
                v.customize ["modifyvm", :id, "--cpus", "2"]
                v.customize ["modifyvm", :id, "--ostype", "Ubuntu_64"]
                v.memory = 1024
        end

        $script = <<SCRIPT
cat /etc/ssh/sshd_config | grep -v -e "^AcceptEnv" > /etc/ssh/sshd_config.new
mv /etc/ssh/sshd_config.new /etc/ssh/sshd_config
service ssh reload
SCRIPT

        config.vm.provision "shell", inline: $script

        config.vm.provision "ansible" do |ansible|
                ansible.playbook = "deployment/site.yml"
                ansible.extra_vars = { app_user: "vagrant" }
                ansible.host_key_checking = false
                #ansible.verbose = "v"
        end
end
