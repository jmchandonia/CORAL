import { SpectatorService, createServiceFactory } from '@ngneat/spectator';
import { GlobalErrorHandler } from './global-error-handler';
import { BsModalRef, BsModalService, ModalModule } from 'ngx-bootstrap/modal';
import { ErrorComponent } from 'src/app/shared/components/error/error.component';

xdescribe('GlobalErrorHandler', () => {
    let spectator: SpectatorService<GlobalErrorHandler>;
    const createService = createServiceFactory({
        service: GlobalErrorHandler,
        providers: [
            BsModalService
        ],
        imports: [
            ModalModule
        ]
    });

    beforeEach(() => spectator = createService());

    it('should create', () => {
        expect(spectator.service).toBeTruthy();
    });

    it('should have handle error method', () => {
        expect(spectator.service.handleError).toBeTruthy();
    });
});
