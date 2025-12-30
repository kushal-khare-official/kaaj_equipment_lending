import { Navigate, useLocation } from 'react-router-dom'

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
    const location = useLocation()
    
    // Check if user is authenticated (mock check)
    const isAuthenticated = localStorage.getItem('auth_token') !== null
    
    if (!isAuthenticated) {
        // Redirect to login page, but save the location they were trying to go to
        return <Navigate to="/login" state={{ from: location }} replace />
    }
    
    return <>{children}</>
}

export function useAuth() {
    const isAuthenticated = localStorage.getItem('auth_token') !== null
    const username = localStorage.getItem('auth_user') || 'Guest'
    
    const logout = () => {
        localStorage.removeItem('auth_token')
        localStorage.removeItem('auth_user')
        window.location.href = '/login'
    }
    
    return { isAuthenticated, username, logout }
}


