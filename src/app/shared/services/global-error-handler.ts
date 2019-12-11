import { Injector, ErrorHandler, Injectable, NgZone } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { BsModalRef, BsModalService } from 'ngx-bootstrap';
import { ErrorComponent } from 'src/app/shared/components/error/error.component';

@Injectable()

export class GlobalErrorHandler implements ErrorHandler {

    private modalRef: BsModalRef;
    private modalService: BsModalService;

    constructor(private injector: Injector, private zone: NgZone) {
        setTimeout(() => {
            this.modalService = this.injector.get(BsModalService);
        });
    }

    handleError(error: Error | HttpErrorResponse) {

        if (error instanceof HttpErrorResponse) {
            const {status, message} = error;
            this.zone.run(() => {
                const config = {
                    class: 'modal-lg',
                    initialState: {status, message}
                };
                this.modalRef = this.modalService.show(ErrorComponent, config);
            });
            console.error(error);
        } else {
            this.zone.run(() => {
                const config = {
                    class: 'modal-lg',
                    initialState: { message: error.message }
                };
                this.modalRef = this.modalService.show(ErrorComponent, config);
            });
            console.error(error);
        }

    }
}
