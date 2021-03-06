import numpy as np
import scipy
from matplotlib.patches import ConnectionPatch


def _line_profile_coordinates(src, dst, linewidth=1):
    """Return the coordinates of the profile of an image along a scan line.
    Parameters
    ----------
    src : 2-tuple of numeric scalar (float or int)
        The start point of the scan line.
    dst : 2-tuple of numeric scalar (float or int)
        The end point of the scan line.
    linewidth : int, optional
        Width of the scan, perpendicular to the line
    Returns
    -------
    coords : array, shape (2, N, C), float
        The coordinates of the profile along the scan line. The length of the
        profile is the ceil of the computed length of the scan line.
    Notes
    -----
    This is a utility method meant to be used internally by skimage functions.
    The destination point is included in the profile, in contrast to
    standard numpy indexing.
    """
    src_row, src_col = src = np.asarray(src, dtype=float)
    dst_row, dst_col = dst = np.asarray(dst, dtype=float)
    d_row, d_col = dst - src
    theta = np.arctan2(d_row, d_col)

    length = int(np.ceil(np.hypot(d_row, d_col) + 1))
    # we add one above because we include the last point in the profile
    # (in contrast to standard numpy indexing)
    line_col = np.linspace(src_col, dst_col, length)
    line_row = np.linspace(src_row, dst_row, length)

    # we subtract 1 from linewidth to change from pixel-counting
    # (make this line 3 pixels wide) to point distances (the
    # distance between pixel centers)
    col_width = (linewidth - 1) * np.sin(-theta) / 2
    row_width = (linewidth - 1) * np.cos(theta) / 2
    perp_rows = np.stack([np.linspace(row_i - row_width, row_i + row_width,
                                    linewidth) for row_i in line_row])
    perp_cols = np.stack([np.linspace(col_i - col_width, col_i + col_width,
                                    linewidth) for col_i in line_col])
    return np.stack([perp_rows, perp_cols])


class LineProfile:
    """
    Class for taking an arbitrary line profile of a 2D dataset. This can be for
    the case of a scanning probe line profile, or a X-ray diffraction reciprocal 
    space map along an arbitrary or crystallographic direction.

    Parameters
    ----------


    Attributes
    ----------

        - p_i       :   tuple, (initial x pixel, initial y pixel)
            Initial pixel points for line profile
        - p_f       :   tuple, (final x pixel, final y pixel)
            Final pixel points for the line profile
        - px_width  :   int
            Width in pixels for the line profile to integrate over. 
        - px_dist   :   int
            Length of the line profile in pixels
        
    """

    def __init__(self, p_i, p_f, width, ):
        self.p_i = p_i
        self.p_f = p_f
        
        self.px_width = width
        self.ln_width_i = None
        self.ln_width_f = None

        # Find distance in pixels of line profile
        self.px_dist = int(np.round(np.hypot(self.p_f[0] - self.p_i[0], self.p_f[1] - self.p_i[0])))
        # Calculate the angle the line makes with the x-axis
        self.line_vec = np.array([self.p_f[0] - self.p_i[0], self.p_f[1] - self.p_i[1]])

        self.angle = np.angle(self.line_vec[0] + self.line_vec[1]*1j, deg=False) 

        # Calculate the offset in X and Y for the linewidth start
        # and end points at the start point for the line profile
        self.xyA_i = (
            (self.p_i[0] - width/2 * np.sin(self.angle)),
            (self.p_i[1] + width/2 * np.cos(self.angle)),
        )
        self.xyB_i = (
            (self.p_i[0] + width/2 * np.sin(self.angle)),
            (self.p_i[1] - width/2 * np.cos(self.angle)),
        )

        self.cpatch_i = ConnectionPatch(
            xyA=self.xyA_i,
            xyB=self.xyB_i,
            coordsA="data",
            coordsB="data",
        )
        
        self.cpatch_line = ConnectionPatch(
            xyA=self.p_i,
            xyB=self.p_f,
            coordsA="data",
            coordsB="data",
        )

        self.xyA_f = (
            (self.p_f[0] - width/2 * np.sin(self.angle)),
            (self.p_f[1] + width/2 * np.cos(self.angle)),
        )
        self.xyB_f = (
            (self.p_f[0] + width/2 * np.sin(self.angle)),
            (self.p_f[1] - width/2 * np.cos(self.angle)),
        )

        self.cpatch_f = ConnectionPatch(
            xyA=self.xyA_f,
            xyB=self.xyB_f,
            coordsA="data",
            coordsB="data",
        )
    def plot_over_channel(self, axis):
        
        
        axis.add_artist(self.cpatch_i)
        axis.add_artist(self.cpatch_line)
        axis.add_artist(self.cpatch_f)
        return axis
    

# Curve fitting functions

# gaussian function
def gaussian(x, amp, mu, std, bg):
    """
    Gaussian function.

    f(x) = amp * exp(-(x-mu)^2/(2*std)^2) + bg

    To get an educated guess of the skewness parameter alpha, use:

    `alpha_guess = scipy.stats.skew(hist_data)` and use this in your 
    initial parameters.
    
    Parameters
    ----------
    x       :   1D np.array
            x-axis array of 
    amp     :   float
            Amplitude of function
    mu      :   float
            Peak centre of function
    std     :   float
            Standard deviation of function


    Returns
    ----------
    output  :   numpy array
            Array of values with length `len(x)`

    """
    
    return amp*np.exp(-np.power(x - mu, 2)/(2 * np.power(std, 2))) + bg

# skewed gaussian
def skewed_gauss(x, amp, mu, std, alpha):
    """
    Skewed Gaussian function.

    f(x) = ....

    To get an educated guess of the skewness parameter alpha, use:

    `alpha_guess = scipy.stats.skew(hist_data)` and use this in your 
    initial parameters.
    

    Parameters
    ----------
    x       :   1D np.array
            x-axis array of 

    amp     :   float
            Amplitude of function
    mu      :   float
            Peak centre of function
    std     :   float
            Standard deviation of function
    alpha   :   float
            Level of skewness of gaussian

    Returns
    ----------
    output  :   numpy array
            Array of values with length `len(x)`

    """
    #normpdf = np.exp(-np.power(x - mu, 2)/(2 * np.power(std, 2)))
    normpdf = (1/(std*np.sqrt(2*np.pi)))*np.exp(-(np.power((x-mu),2)/(2*np.power(std,2))))
    normcdf = (0.5*(1+scipy.special.erf((alpha*((x - mu)/std))/(np.sqrt(2)))))
    return 2*amp*normpdf*normcdf

# rayleigh distribution
def rayleigh(x, amp, sigma, bg):
    return amp*x*np.exp((-x**2/(2*sigma**2)))*(1/sigma**2) + bg

# exponential distribution
def exp_dist(x, A, beta):
    return A * np.exp(-x/beta) 

# lorentz distribution
def lorentz(x, amp, width, xc, bg):
    return amp*(1/np.pi) * (0.5 * width)/((x - xc)**2 + (0.5*width)**2)

#line 
def line(x, a, b):
    return a*x + b 

#parabola 
def parabola(x, a, b, c):
    return a*x**2 + b*x + c

# second degree polynomial 
def second_poly(x, a, b, c):
    return a*x**2 + b*x + c 

# cubic polynomial 
def cubic(x, a, b, c, d):
    return a*x**3 + b*x**2 + c*x + d 

# exponential 
def exp(x, a, b):
    return a*np.exp(b*x)

# logarithmic 
def log(x, a, b):
    return a*np.log(x) + b 

# sine wave 
def sine(x, a, b, c, d):
    return a*np.sin(b*x + c) + d


# cosine wave 
def cosine(x, a, b, c, d):
    return a*np.cos(b*x + c) + d