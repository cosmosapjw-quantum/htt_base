import edu.jas.arith.BigRational;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * Exact Java Algebra System verification for PMG-WU-011 Task-7C.
 *
 * <p>The calculation uses unnormalised associated-Legendre functions.  All
 * omitted spherical-harmonic normalisations are nonzero diagonal row/column
 * scalings, so they cannot alter rank.  Products P_l^m P_j^m are represented
 * exactly as
 *
 * <pre>
 * (1-x^2)^m D^m P_l(x) D^m P_j(x),
 * </pre>
 *
 * and integrated against the exact piecewise-rational wide mask.  The
 * z-directed first-order boost generator is
 *
 * <pre>
 * G_z P_l^m = ((l+1)(l-m+1)/(2l+1)) P_{l+1}^m
 *             -(l(l+m)/(2l+1)) P_{l-1}^m.
 * </pre>
 *
 * <p>This program verifies exact block ranks for source cutoffs L=8,9,12 and
 * writes an exact-rational receipt.  It does not fit beta or authorize a
 * scientific terminal.
 */
public final class WU011JASExact {
    private static final BigRational ZERO = new BigRational(0);
    private static final BigRational ONE = new BigRational(1);
    private static final List<BigRational[]> LEGENDRE = new ArrayList<>();

    static {
        LEGENDRE.add(poly(ONE));
        LEGENDRE.add(poly(ZERO, ONE));
    }

    private WU011JASExact() {}

    private static BigRational q(long numerator) {
        return new BigRational(numerator);
    }

    private static BigRational q(long numerator, long denominator) {
        return new BigRational(numerator, denominator);
    }

    private static BigRational[] poly(BigRational... coefficients) {
        return coefficients;
    }

    private static BigRational[] zeros(int size) {
        BigRational[] result = new BigRational[size];
        Arrays.fill(result, ZERO);
        return result;
    }

    private static BigRational[] add(BigRational[] first, BigRational[] second) {
        BigRational[] result = zeros(Math.max(first.length, second.length));
        for (int i = 0; i < result.length; ++i) {
            BigRational a = i < first.length ? first[i] : ZERO;
            BigRational b = i < second.length ? second[i] : ZERO;
            result[i] = a.sum(b);
        }
        return result;
    }

    private static BigRational[] scale(BigRational[] value, BigRational factor) {
        BigRational[] result = zeros(value.length);
        for (int i = 0; i < value.length; ++i) {
            result[i] = value[i].multiply(factor);
        }
        return result;
    }

    private static BigRational[] shift(BigRational[] value) {
        BigRational[] result = zeros(value.length + 1);
        System.arraycopy(value, 0, result, 1, value.length);
        return result;
    }

    private static BigRational[] multiply(BigRational[] first, BigRational[] second) {
        BigRational[] result = zeros(first.length + second.length - 1);
        for (int i = 0; i < first.length; ++i) {
            for (int j = 0; j < second.length; ++j) {
                result[i + j] = result[i + j].sum(first[i].multiply(second[j]));
            }
        }
        return result;
    }

    private static BigRational[] derivative(BigRational[] value, int order) {
        BigRational[] result = value;
        for (int step = 0; step < order; ++step) {
            if (result.length <= 1) {
                return poly(ZERO);
            }
            BigRational[] next = zeros(result.length - 1);
            for (int power = 1; power < result.length; ++power) {
                next[power - 1] = result[power].multiply(q(power));
            }
            result = next;
        }
        return result;
    }

    private static BigRational[] oneMinusXSquaredPower(int power) {
        BigRational[] result = poly(ONE);
        BigRational[] factor = poly(ONE, ZERO, q(-1));
        for (int i = 0; i < power; ++i) {
            result = multiply(result, factor);
        }
        return result;
    }

    private static BigRational[] legendre(int degree) {
        while (LEGENDRE.size() <= degree) {
            int ell = LEGENDRE.size();
            BigRational[] first = scale(
                shift(LEGENDRE.get(ell - 1)), q(2L * ell - 1L, ell)
            );
            BigRational[] second = scale(
                LEGENDRE.get(ell - 2), q(-(ell - 1L), ell)
            );
            LEGENDRE.add(add(first, second));
        }
        return LEGENDRE.get(degree);
    }

    private static BigRational power(BigRational base, int exponent) {
        BigRational result = ONE;
        for (int i = 0; i < exponent; ++i) {
            result = result.multiply(base);
        }
        return result;
    }

    private static BigRational integratePolynomial(
        BigRational[] coefficients,
        BigRational lower,
        BigRational upper
    ) {
        BigRational result = ZERO;
        for (int power = 0; power < coefficients.length; ++power) {
            BigRational factor = coefficients[power].divide(q(power + 1L));
            BigRational delta = power(upper, power + 1).subtract(
                power(lower, power + 1)
            );
            result = result.sum(factor.multiply(delta));
        }
        return result;
    }

    private static BigRational integrateWideMask(BigRational[] polynomial) {
        BigRational[] middleMask = poly(q(1, 2), q(2, 3));
        BigRational middle = integratePolynomial(
            multiply(polynomial, middleMask), q(-3, 4), q(3, 4)
        );
        BigRational upper = integratePolynomial(polynomial, q(3, 4), ONE);
        return middle.sum(upper);
    }

    private static BigRational associatedProductIntegral(int ell, int j, int m) {
        if (ell < m || j < m || ell < 0 || j < 0) {
            return ZERO;
        }
        BigRational[] first = derivative(legendre(ell), m);
        BigRational[] second = derivative(legendre(j), m);
        BigRational[] product = multiply(
            oneMinusXSquaredPower(m), multiply(first, second)
        );
        return integrateWideMask(product);
    }

    private static BigRational[][] buildNormal(int m) {
        int size = 6 - m;
        BigRational[][] normal = new BigRational[size][size];
        for (int row = 0; row < size; ++row) {
            int ell = m + row;
            for (int col = 0; col < size; ++col) {
                int j = m + col;
                normal[row][col] = associatedProductIntegral(ell, j, m);
            }
        }
        return normal;
    }

    private static BigRational[][] buildRightHandSide(int m, int sourceCutoff) {
        int rows = 6 - m;
        int columns = sourceCutoff - 6;
        BigRational[][] rhs = new BigRational[rows][columns];
        for (int row = 0; row < rows; ++row) {
            int fitEll = m + row;
            for (int col = 0; col < columns; ++col) {
                int sourceEll = 7 + col;
                BigRational up = q(
                    (long) (sourceEll + 1) * (sourceEll - m + 1),
                    2L * sourceEll + 1L
                );
                BigRational down = q(
                    -(long) sourceEll * (sourceEll + m),
                    2L * sourceEll + 1L
                );
                rhs[row][col] = up.multiply(
                    associatedProductIntegral(fitEll, sourceEll + 1, m)
                ).sum(
                    down.multiply(
                        associatedProductIntegral(fitEll, sourceEll - 1, m)
                    )
                );
            }
        }
        return rhs;
    }

    private static BigRational[][] solve(
        BigRational[][] matrix,
        BigRational[][] rhs
    ) {
        int n = matrix.length;
        int columns = rhs[0].length;
        BigRational[][] augmented = new BigRational[n][n + columns];
        for (int row = 0; row < n; ++row) {
            System.arraycopy(matrix[row], 0, augmented[row], 0, n);
            System.arraycopy(rhs[row], 0, augmented[row], n, columns);
        }
        for (int pivotColumn = 0; pivotColumn < n; ++pivotColumn) {
            int pivotRow = pivotColumn;
            while (pivotRow < n && augmented[pivotRow][pivotColumn].isZERO()) {
                ++pivotRow;
            }
            if (pivotRow == n) {
                throw new IllegalStateException("exact normal matrix is singular");
            }
            BigRational[] temporary = augmented[pivotColumn];
            augmented[pivotColumn] = augmented[pivotRow];
            augmented[pivotRow] = temporary;

            BigRational pivot = augmented[pivotColumn][pivotColumn];
            for (int col = pivotColumn; col < n + columns; ++col) {
                augmented[pivotColumn][col] = augmented[pivotColumn][col].divide(pivot);
            }
            for (int row = 0; row < n; ++row) {
                if (row == pivotColumn) {
                    continue;
                }
                BigRational factor = augmented[row][pivotColumn];
                if (factor.isZERO()) {
                    continue;
                }
                for (int col = pivotColumn; col < n + columns; ++col) {
                    augmented[row][col] = augmented[row][col].subtract(
                        factor.multiply(augmented[pivotColumn][col])
                    );
                }
            }
        }
        BigRational[][] result = new BigRational[n][columns];
        for (int row = 0; row < n; ++row) {
            System.arraycopy(augmented[row], n, result[row], 0, columns);
        }
        return result;
    }

    private static BigRational[][] retainedRows(BigRational[][] fitted, int m) {
        int firstEll = Math.max(2, m);
        int start = firstEll - m;
        int rows = 6 - firstEll;
        BigRational[][] retained = new BigRational[rows][fitted[0].length];
        for (int row = 0; row < rows; ++row) {
            System.arraycopy(
                fitted[start + row], 0, retained[row], 0, fitted[0].length
            );
        }
        return retained;
    }

    private static final class RankResult {
        final int rank;
        final int[] pivotColumns;

        RankResult(int rank, int[] pivotColumns) {
            this.rank = rank;
            this.pivotColumns = pivotColumns;
        }
    }

    private static RankResult rankAndPivots(BigRational[][] input) {
        int rows = input.length;
        int columns = input[0].length;
        BigRational[][] matrix = new BigRational[rows][columns];
        for (int row = 0; row < rows; ++row) {
            matrix[row] = input[row].clone();
        }
        List<Integer> pivots = new ArrayList<>();
        int pivotRow = 0;
        for (int col = 0; col < columns && pivotRow < rows; ++col) {
            int selected = pivotRow;
            while (selected < rows && matrix[selected][col].isZERO()) {
                ++selected;
            }
            if (selected == rows) {
                continue;
            }
            BigRational[] temporary = matrix[pivotRow];
            matrix[pivotRow] = matrix[selected];
            matrix[selected] = temporary;
            BigRational pivot = matrix[pivotRow][col];
            for (int j = col; j < columns; ++j) {
                matrix[pivotRow][j] = matrix[pivotRow][j].divide(pivot);
            }
            for (int row = 0; row < rows; ++row) {
                if (row == pivotRow) {
                    continue;
                }
                BigRational factor = matrix[row][col];
                if (factor.isZERO()) {
                    continue;
                }
                for (int j = col; j < columns; ++j) {
                    matrix[row][j] = matrix[row][j].subtract(
                        factor.multiply(matrix[pivotRow][j])
                    );
                }
            }
            pivots.add(col);
            ++pivotRow;
        }
        int[] pivotArray = pivots.stream().mapToInt(Integer::intValue).toArray();
        return new RankResult(pivotRow, pivotArray);
    }

    private static BigRational determinant(BigRational[][] input) {
        int n = input.length;
        BigRational[][] matrix = new BigRational[n][n];
        for (int row = 0; row < n; ++row) {
            matrix[row] = input[row].clone();
        }
        BigRational determinant = ONE;
        int sign = 1;
        for (int col = 0; col < n; ++col) {
            int pivotRow = col;
            while (pivotRow < n && matrix[pivotRow][col].isZERO()) {
                ++pivotRow;
            }
            if (pivotRow == n) {
                return ZERO;
            }
            if (pivotRow != col) {
                BigRational[] temporary = matrix[col];
                matrix[col] = matrix[pivotRow];
                matrix[pivotRow] = temporary;
                sign = -sign;
            }
            BigRational pivot = matrix[col][col];
            determinant = determinant.multiply(pivot);
            for (int row = col + 1; row < n; ++row) {
                BigRational factor = matrix[row][col].divide(pivot);
                for (int j = col; j < n; ++j) {
                    matrix[row][j] = matrix[row][j].subtract(
                        factor.multiply(matrix[col][j])
                    );
                }
            }
        }
        return sign < 0 ? determinant.negate() : determinant;
    }

    private static BigRational fullRowMinor(
        BigRational[][] matrix,
        int[] pivotColumns
    ) {
        int rows = matrix.length;
        if (pivotColumns.length != rows) {
            return ZERO;
        }
        BigRational[][] square = new BigRational[rows][rows];
        for (int row = 0; row < rows; ++row) {
            for (int col = 0; col < rows; ++col) {
                square[row][col] = matrix[row][pivotColumns[col]];
            }
        }
        return determinant(square);
    }

    private static int expectedBlockRank(int cutoff, int m) {
        if (cutoff == 8) {
            return new int[] {2, 2, 2, 2, 2, 1}[m];
        }
        if (cutoff == 9) {
            return new int[] {3, 3, 3, 3, 2, 1}[m];
        }
        if (cutoff == 12) {
            return new int[] {4, 4, 4, 3, 2, 1}[m];
        }
        throw new IllegalArgumentException("unregistered source cutoff");
    }

    public static void main(String[] args) throws IOException {
        Path outputDirectory = args.length == 0
            ? Path.of("external_cas_results")
            : Path.of(args[0]);
        Files.createDirectories(outputDirectory);

        StringBuilder csv = new StringBuilder();
        csv.append("source_cutoff,m,output_rows,source_columns,exact_rank,")
            .append("full_row_minor_nonzero,full_row_minor\n");

        int[] cutoffs = {8, 9, 12};
        for (int cutoff : cutoffs) {
            int totalRealRank = 0;
            for (int m = 0; m <= 5; ++m) {
                BigRational[][] normal = buildNormal(m);
                BigRational[][] rhs = buildRightHandSide(m, cutoff);
                BigRational[][] fitted = solve(normal, rhs);
                BigRational[][] response = retainedRows(fitted, m);
                RankResult rank = rankAndPivots(response);
                int expected = expectedBlockRank(cutoff, m);
                if (rank.rank != expected) {
                    throw new AssertionError(
                        "unexpected exact block rank at L=" + cutoff
                        + ", m=" + m + ": " + rank.rank
                        + " != " + expected
                    );
                }
                totalRealRank += m == 0 ? rank.rank : 2 * rank.rank;
                BigRational minor = fullRowMinor(response, rank.pivotColumns);
                boolean fullRow = rank.rank == response.length;
                if (fullRow && minor.isZERO()) {
                    throw new AssertionError("pivot minor unexpectedly vanishes");
                }
                csv.append(cutoff).append(',')
                    .append(m).append(',')
                    .append(response.length).append(',')
                    .append(response[0].length).append(',')
                    .append(rank.rank).append(',')
                    .append(fullRow && !minor.isZERO()).append(',')
                    .append(fullRow ? minor.toString() : "")
                    .append('\n');
            }
            int expectedTotal = cutoff == 8 ? 20 : cutoff == 9 ? 27 : 32;
            if (totalRealRank != expectedTotal) {
                throw new AssertionError(
                    "unexpected total exact rank at L=" + cutoff + ": "
                    + totalRealRank + " != " + expectedTotal
                );
            }
            System.out.println(
                "JAS exact wide-mask z-axis rank: L=" + cutoff
                + ", stored-real rank=" + totalRealRank
            );
        }

        Files.writeString(
            outputDirectory.resolve("jas_exact_z_block_ranks.csv"),
            csv.toString(),
            StandardCharsets.UTF_8
        );
        Files.writeString(
            outputDirectory.resolve("jas_status.txt"),
            "PASS_JAS_EXACT_Z_AXIS_RANK_L12_32\n",
            StandardCharsets.UTF_8
        );
    }
}
