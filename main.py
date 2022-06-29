import pygame
import bricks


def main():
    pygame.init()
    pygame.font.init()
    pygame.mixer.init()

    bricks.App(1280, 720, 60).run()


if __name__ == '__main__':
    main()
