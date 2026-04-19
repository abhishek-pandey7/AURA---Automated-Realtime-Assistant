#include <iostream>

int main() {
    for (int i = 1; i <= 100; ++i) {
        std::cout << i << (i == 100 ? "" : " ");
    }
    std::cout << std::endl;
    return 0;
}
