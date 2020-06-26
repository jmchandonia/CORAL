import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory } from '@ngneat/spectator';
import { ContextBuilderComponent } from './context-builder.component';
import { MockComponent } from 'ng-mocks';
import { ContextFormComponent } from './context-form/context-form.component';
import { ModalModule, BsModalRef } from 'ngx-bootstrap/modal';
import { HttpClientModule } from '@angular/common/http';
const metadata = require('src/app/shared/test/brick-type-templates.json');
import { BrickFactoryService } from 'src/app/shared/services/brick-factory.service';
import { Context } from 'src/app/shared/models/brick';
import { UploadValidationService } from 'src/app/shared/services/upload-validation.service';

describe('ContextBuilderComponent', () => {

  const brick = BrickFactoryService.createUploadInstance(metadata.results[0].children[1]);
  const dataValue = brick.dataValues[0];

  let spectator: Spectator<ContextBuilderComponent>;
  const createComponent = createComponentFactory({
    component: ContextBuilderComponent,
    entryComponents: [
      MockComponent(ContextFormComponent)
    ],
    imports: [
      ModalModule.forRoot(),
      HttpClientModule
    ],
    providers: [
      BsModalRef,
      {
        provide: UploadValidationService,
        useValue: {
          validateContext: (context) => [
            'error message 1',
            'error message 2'
          ]
        }
      }
    ]
  });

  beforeEach(() => spectator = createComponent({
    props: {
      context: dataValue.context
    }
  }));

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
    expect(spectator.component.context).toHaveLength(0);
  });

  it('should add context', () => {
    spyOn(spectator.component, 'addContext').and.callThrough();
    spectator.click('button#add-context');
    spectator.detectChanges();

    expect(spectator.component.addContext).toHaveBeenCalled();
    expect(spectator.component.context).toHaveLength(1);
    expect(dataValue.context).toHaveLength(1);
    expect(spectator.queryAll('app-context-form')).toHaveLength(1);
  });

  it('should reset context', () => {
    spyOn(spectator.component, 'resetContext').and.callThrough();
    spectator.component.addContext();
    spectator.detectChanges();
    spectator.component.context[0].scalarType = 'test';

    spectator.triggerEventHandler('app-context-form', 'resetContext', new Context());
    spectator.detectChanges();
    expect(spectator.component.resetContext).toHaveBeenCalledWith(new Context(), 0);
    expect(spectator.component.context[0].scalarType).toBeUndefined();
  });

  it('should remove context', () => {
    spyOn(spectator.component, 'removeContext').and.callThrough();
    spectator.triggerEventHandler('app-context-form', 'deleted', null);
    spectator.detectChanges();

    expect(spectator.component.removeContext).toHaveBeenCalledWith(0);
    expect(spectator.component.context).toHaveLength(1);
    expect(spectator.queryAll('app-context-form')).toHaveLength(1);
  });

  it('should receive error messages from child components', () => {
    spyOn(spectator.component, 'setValueError').and.callThrough();
    spectator.triggerEventHandler('app-context-form', 'valueError', 'this is broken!');
    spectator.detectChanges();

    expect(spectator.component.errorMessages).toHaveLength(1);
    expect(spectator.queryAll('div.alert.alert-danger')).toHaveLength(1);
    expect(spectator.component.errorMessages[0]).toBe('this is broken!');
  });

  it('should validate errors on close', () => {
    const validator = spectator.get(UploadValidationService);
    spyOn(validator, 'validateContext').and.callThrough();
    spyOn(spectator.component, 'onClose').and.callThrough();

    spectator.click('button#close-context-modal');
    expect(spectator.component.onClose).toHaveBeenCalled();
    expect(validator.validateContext).toHaveBeenCalled();
    expect(spectator.component.error).toBeTruthy();
    expect(spectator.component.errorMessages).toHaveLength(2);
  })
});
