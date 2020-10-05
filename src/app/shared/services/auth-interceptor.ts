import { Injectable } from '@angular/core';
import {
    HttpEvent,
    HttpRequest,
    HttpHandler,
    HttpInterceptor,
} from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable()

export class AuthInterceptor implements HttpInterceptor {

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

        return next.handle(request);
    }

}