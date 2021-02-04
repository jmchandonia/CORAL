import { Injectable } from '@angular/core';
import {
    HttpEvent,
    HttpRequest,
    HttpHandler,
    HttpInterceptor,
    HttpErrorResponse,
} from '@angular/common/http';
import { Observable, of, empty, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { Router } from '@angular/router';

@Injectable()

export class AuthInterceptor implements HttpInterceptor {

    constructor(private router: Router) {}

    intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {

        const authToken = localStorage.getItem('authToken');

        if (authToken === null) {
            return next.handle(request);
        }

        request = request.clone({
            setHeaders: {
                'Authorization' : `Bearer ${localStorage.getItem('authToken')}`
            }
        });

        return next.handle(request).pipe(catchError(e => this.handleAuthError(e)));
    }

    handleAuthError(error: HttpErrorResponse): Observable<any> {
        if (error.status === 401 || error.status === 403) {
            // localStorage.clear();
            localStorage.removeItem('authToken');
            this.router.navigate(['/login']);
            return of(empty());
        }
        return throwError(error);
    }

}