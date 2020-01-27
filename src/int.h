#ifndef INT_H
#define INT_H

template <typename T, typename S>
T numeric_cast(S x) {
    static_assert(std::numeric_limits<S>::is_integer, "argument type is not an integer");
    static_assert(std::numeric_limits<T>::is_integer, "return type is not an integer");

    constexpr bool sS = std::numeric_limits<S>::is_signed;
    constexpr bool sT = std::numeric_limits<T>::is_signed;
    if (sS && !sT) {
        assert(x >= 0);
    }

    assert(x <= std::numeric_limits<T>::max());

    return static_cast<T>(x);
}

#endif // !INT_H
