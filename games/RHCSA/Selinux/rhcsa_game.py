#!/usr/bin/env python3
import sys
import random
import textwrap

# ===============================
#   GLOBAL GAME ENGINE
# ===============================

score = 0

def banner(title):
    print("\n" + "="*60)
    print(title)
    print("="*60 + "\n")

def prompt(cmd="> "):
    return input(cmd).strip()

def correct(msg="Correct!"):
    global score
    score += 1
    print("✅ " + msg + "\n")

def wrong(msg="Incorrect."):
    print("❌ " + msg + "\n")

def ask_hint(hint):
    h = prompt("Need a hint? (y/n): ")
    if h.lower().startswith("y"):
        print("💡 Hint: " + hint + "\n")

# ===============================
#   PERMISSIONS MODULE
# ===============================

def permissions_module():
    banner("PERMISSION MASTER – SUID / SGID / Sticky Bit / chmod")

    levels = [
        {
            "desc": "Make script.sh executable by owner only.",
            "ls": "-rw-rw-r-- script.sh",
            "answer": "chmod 700 script.sh",
            "hint": "Owner should have rwx, others none."
        },
        {
            "desc": "Set the SUID bit on /usr/bin/custom",
            "ls": "-rwxr-xr-x custom",
            "answer": "chmod u+s /usr/bin/custom",
            "hint": "Use chmod u+s filename"
        },
        {
            "desc": "Set SGID on /shared so files inherit group.",
            "ls": "drwxrwxr-x shared",
            "answer": "chmod g+s /shared",
            "hint": "Add SGID with g+s"
        },
        {
            "desc": "Set Sticky Bit on /public",
            "ls": "drwxrwxrwx public",
            "answer": "chmod +t /public",
            "hint": "Only root can remove files in sticky directories"
        },
    ]

    for lvl in levels:
        print("Scenario:", lvl["desc"])
        print("Current:", lvl["ls"])
        cmd = prompt()

        if cmd == lvl["answer"]:
            correct()
        else:
            wrong()
            ask_hint(lvl["hint"])

# ===============================
#   ACL MODULE
# ===============================

def acl_module():
    banner("ACL SURVIVAL MODE – setfacl / getfacl / masks")

    scenarios = [
        {
            "desc": "Give user alice rwx on project.txt",
            "answer": "setfacl -m u:alice:rwx project.txt",
            "hint": "Use: setfacl -m u:<user>:<perms> file"
        },
        {
            "desc": "Set default ACL so bob gets rwx on all new files in /shared",
            "answer": "setfacl -d -m u:bob:rwx /shared",
            "hint": "-d means default; acts only on directories"
        },
        {
            "desc": "Remove alice ACL from project.txt",
            "answer": "setfacl -x u:alice project.txt",
            "hint": "Use -x to remove ACL entries"
        }
    ]

    for sc in scenarios:
        print("Scenario:", sc["desc"])
        cmd = prompt()

        if cmd == sc["answer"]:
            correct()
        else:
            wrong()
            ask_hint(sc["hint"])

# ===============================
#   SELINUX MODULE
# ===============================

def selinux_module():
    banner("SELINUX DUNGEON – contexts / restorecon / semanage")

    levels = [
        {
            "desc": "Make Apache serve files from /virtual permanently.",
            "answers": [
                "semanage fcontext -a -t httpd_sys_content_t '/virtual(/.*)?'",
                "restorecon -Rv /virtual"
            ],
            "hint": "Use semanage fcontext + restorecon."
        },
        {
            "desc": "Temporary change: label /tmp/test as httpd_sys_rw_content_t",
            "answers": [
                "chcon -t httpd_sys_rw_content_t /tmp/test"
            ],
            "hint": "chcon is temporary; not persistent."
        },
        {
            "desc": "Enable boolean to allow Apache to access NFS content.",
            "answers": [
                "setsebool -P httpd_use_nfs on"
            ],
            "hint": "Use setsebool -P <boolean> on"
        }
    ]

    for lvl in levels:
        print("Scenario:", lvl["desc"])
        cmds = []
        print("Enter commands (blank to finish):")
        while True:
            c = prompt("")
            if not c:
                break
            cmds.append(c)

        # Check if all required answers are in user's commands
        if all(ans in cmds for ans in lvl["answers"]):
            correct()
        else:
            wrong()
            ask_hint(lvl["hint"])

# ===============================
#   RD.BREAK / ROOT PASSWORD MODULE
# ===============================

def rescue_module():
    banner("BOOT RESCUE SIMULATOR – rd.break / chroot / passwd")

    steps = [
        ("Press e at GRUB", ["e"]),
        ("Append rd.break to kernel line", ["rd.break"]),
        ("Remount sysroot RW", ["mount -o remount,rw /sysroot"]),
        ("Chroot into sysroot", ["chroot /sysroot"]),
        ("Reset root password", ["passwd root"]),
        ("Force SELinux relabel", ["touch /.autorelabel"]),
        ("Exit chroot", ["exit"]),
        ("Exit emergency shell", ["exit"])
    ]

    for desc, answers in steps:
        print("\nTask:", desc)
        cmd = prompt("> ")

        if cmd in answers:
            correct()
        else:
            wrong()
            ask_hint("Think through the RHCSA rd.break workflow.")

# ===============================
#   MAIN MENU
# ===============================

def main():
    banner("🔥 RHCSA COMMAND-LINE TRAINER GAME 🔥")
    print("Choose a module:\n")
    print("1) Permissions Master")
    print("2) ACL Survival Mode")
    print("3) SELinux Dungeon")
    print("4) rd.break Rescue Simulator")
    print("5) Quit\n")

    choice = prompt("Select: ")

    if choice == "1":
        permissions_module()
    elif choice == "2":
        acl_module()
    elif choice == "3":
        selinux_module()
    elif choice == "4":
        rescue_module()
    else:
        print("\nFinal Score:", score)
        print("Goodbye!")
        sys.exit(0)

    # Loop
    main()

if __name__ == "__main__":
    main()
# End of File