# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
    # All Vagrant configuration is done here. The most common configuration
    # options are documented and commented below. For a complete reference,
    # please see the online documentation at vagrantup.com.

    config.vm.synced_folder ".", "/vagrant", type: "rsync", 
        rsync__exclude: ".git/", rsync__args: ["--verbose", "--archive", "--delete", "-z", "--links"]

    # Every Vagrant virtual environment requires a box to build off of.
    config.vm.box = "trusty64"

    # The url from where the 'config.vm.box' box will be fetched if it
    # doesn't already exist on the user's system.
    config.vm.box_url = "https://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-amd64-vagrant-disk1.box"

    if Vagrant.has_plugin?("vagrant-cachier")
        # Configure cached packages to be shared between instances of the same base box.
        # More info on http://fgrehm.viewdocs.io/vagrant-cachier/usage
        config.cache.scope = :box
    end

    config.vm.provider "virtualbox" do |vb|
      vb.customize ["modifyvm", :id, "--memory", "1024"]
    end
    config.vm.provider :libvirt do |lv|
      lv.memory = 1024
    end

    config.vm.provision "ansible" do |ansible|
        ansible.playbook = "test.yml"
    end

end
