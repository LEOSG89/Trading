def generar_combinaciones_contratos(n, k=4):
    """
    Genera todas las composiciones de n en k partes (enteros >= 0).
    Cada composición es una lista de longitud k cuya suma es n.
    Devuelve la lista completa de composiciones.
    """
    comps = []
    def helper(prefix, parts_left, sum_left):
        if parts_left == 1:
            comps.append(prefix + [sum_left])
        else:
            for i in range(sum_left + 1):
                helper(prefix + [i], parts_left - 1, sum_left - i)
    helper([], k, n)
    return comps
