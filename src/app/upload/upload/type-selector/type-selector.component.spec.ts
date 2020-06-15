import { async, ComponentFixture, TestBed, fakeAsync } from '@angular/core/testing';
import { Spectator, createComponentFactory, mockProvider } from '@ngneat/spectator';
import { TypeSelectorComponent } from './type-selector.component';
import { NgSelectModule } from '@ng-select/ng-select';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { UploadService } from 'src/app/shared/services/upload.service';
import { UploadValidationService } from 'src/app/shared/services/upload-validation.service';
import { Brick } from 'src/app/shared/models/brick';
import { of, Subject } from 'rxjs';
const testTemplates = require('src/app/shared/test/brick-type-templates.json');

describe('TypeSelectorComponent', () => {

  const MockUploadService = {
    getBrickBuilder: () => new Brick(),
    getTemplateSub: () =>  of(testTemplates.results)
  }

  const errorSub = new Subject();

  const MockValidator = {
    getValidationErrors: () => errorSub,
    validateDataType: () => {}
  }

  let spectator: Spectator<TypeSelectorComponent>;
  let createComponent = createComponentFactory({
    component: TypeSelectorComponent,
    imports: [
      HttpClientModule,
      NgSelectModule,
      FormsModule
    ],
    providers: [
      mockProvider(UploadService, MockUploadService),
      mockProvider(UploadValidationService, MockValidator)
    ]
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });

  it('should have brickbuilder instance', () => {
    expect(spectator.component.brick).not.toBeUndefined();
    expect(spectator.component.brick instanceof Brick).toBeTruthy();
  });

  it('should populate template dropdown', () => {
    const { templateData } = spectator.component;
    expect(templateData).toHaveLength(1);
    expect(templateData[0].children).toHaveLength(2);
    expect(templateData[0].children[0].text).toBe('Custom Chemical Measurement');
  });

  it('should set selected template in service', () => {
    const uploadService = spectator.fixture.debugElement.injector.get(UploadService);
    spyOn(spectator.component, 'validate');
    spectator.component.setBrickType({test: 'test'});
    spectator.detectChanges();
    expect(uploadService.setSelectedTemplate).toHaveBeenCalledWith({test: 'test'});
    expect(spectator.component.validate).toHaveBeenCalled();
  });

  it('should receive and display errors from validator', async(() => {
    const validator = spectator.fixture.debugElement.injector.get(UploadValidationService);
    spyOn(validator, 'validateDataType');
    spectator.fixture.whenStable().then(() => {
      errorSub.next(true);
      spectator.detectChanges();
      expect(spectator.component.error).toBeTruthy();
      expect(spectator.query('div.alert.alert-danger')).toBeTruthy();

      // call validation 
      spectator.component.validate();
      expect(validator.validateDataType).toHaveBeenCalled();
    });
  }));
});
