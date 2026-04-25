from modules.xarm import XArmAPI


def main():
    arm = XArmAPI("192.168.1.241")
    arm.motion_enable(enable=True)
    arm.set_mode(2)
    arm.set_state(state=0)
    arm.clean_warn()
    arm.clean_error()

    while True:
        ipt = input("按回车键采集，输入任意字符结束: ")
        if ipt:
            break

        pos = arm.get_position()[1][0:3]
        print(f"Tgt: ({pos})")
        print()


if __name__ == '__main__':
    main()
