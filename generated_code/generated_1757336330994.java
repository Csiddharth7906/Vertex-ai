// FlappyBird.java
import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import java.util.Random;

public class FlappyBird extends JPanel implements KeyListener {
    private int birdX = 100;
    private int birdY = 100;
    private int birdVel = 0;
    private int pipeX = 400;
    private int pipeY = 200;
    private int pipeVel = 2;
    private boolean gameOver = false;
    private boolean isJumping = false;

    public FlappyBird() {
        setFocusable(true);
        addKeyListener(this);
        Timer timer = new Timer(16, e -> {
            if (!gameOver) {
                birdVel += 0.1;
                birdY += birdVel;
                pipeX -= pipeVel;

                if (pipeX < -20) {
                    pipeX = 400;
                    pipeY = new Random().nextInt(200);
                }

                if (birdY > 500 || birdY < 0) {
                    gameOver = true;
                }

                if (pipeX < birdX + 20 && pipeX + 20 > birdX && (birdY < pipeY || birdY + 20 > pipeY + 200)) {
                    gameOver = true;
                }
            }
            repaint();
        });
        timer.start();
    }

    @Override
    public void paintComponent(Graphics g) {
        super.paintComponent(g);
        g.setColor(Color.BLACK);
        g.fillRect(0, 0, 800, 600);
        g.setColor(Color.WHITE);
        g.fillOval(birdX, birdY, 20, 20);
        g.fillRect(pipeX, 0, 20, pipeY);
        g.fillRect(pipeX, pipeY + 200, 20, 600 - pipeY - 200);
        g.setFont(new Font("Arial", Font.BOLD, 24));
        g.drawString("Score: " + (pipeX / 2), 10, 30);
        if (gameOver) {
            g.drawString("Game Over!", 300, 300);
        }
    }

    @Override
    public void keyPressed(KeyEvent e) {
        if (e.getKeyCode() == KeyEvent.VK_SPACE && !isJumping) {
            birdVel = -5;
            isJumping = true;
        }
    }

    @Override
    public void keyReleased(KeyEvent e) {
        if (e.getKeyCode() == KeyEvent.VK_SPACE) {
            isJumping = false;
        }
    }

    @Override
    public void keyTyped(KeyEvent e) {
    }

    public static void main(String[] args) {
        JFrame frame = new JFrame("Flappy Bird");
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.setSize(800, 600);
        frame.add(new FlappyBird());
        frame.setVisible(true);
    }
}