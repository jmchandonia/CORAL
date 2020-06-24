import { async, ComponentFixture, TestBed, tick, fakeAsync } from '@angular/core/testing';
import { Spectator, createComponentFactory, mockProvider } from '@ngneat/spectator';
import { TooltipModule } from 'ngx-bootstrap/tooltip';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { BsModalService, ModalModule } from 'ngx-bootstrap/modal';
import { PropertyFormComponent } from './property-form.component';
import { TypedProperty, Brick, MicroType } from 'src/app/shared/models/brick';
import { Subject, of, Observable, asyncScheduler } from 'rxjs';
import { BrickFactoryService } from 'src/app/shared/services/brick-factory.service';
import { UploadValidationService } from 'src/app/shared/services/upload-validation.service';
import { UploadService } from 'src/app/shared/services/upload.service';
import { By } from '@angular/platform-browser';
import { ContextBuilderComponent } from './context-builder/context-builder.component';
import { MockComponent } from 'ng-mocks';
import { NgSelectModule } from '@ng-select/ng-select';
const metadata = require('src/app/shared/test/brick-type-templates.json');

describe('PropertyFormComponent', () => {

  const brick: Brick = BrickFactoryService.createUploadInstance(metadata.results[0].children[1]);
  const properties: TypedProperty[] = brick.properties;
  let property: TypedProperty = brick.properties[0];
  const errorSub = new Subject();

  const MockUploadService = {
    searchOntPropertyUnits: (microtype:MicroType): Observable<any> => of({
      results: property === brick.properties[0] ? [] : [{id: 'abcd', text: 'test unit'}]
    }),
  };

  const MockValidator = {
    getValidationErrors: () => errorSub,
    validScalarType: () => false,
    INVALID_VALUE: 'invalid value'
  }

  const MockModal = {
    show: () => {},
    onHidden: of({}, asyncScheduler)
  }

  let spectator: Spectator<PropertyFormComponent>;
  const createComponent = createComponentFactory({
    component: PropertyFormComponent,
    imports: [
      TooltipModule.forRoot(),
      FormsModule,
      NgSelectModule,
      HttpClientModule,
      ModalModule 
    ],
    providers: [
      BsModalService,
      mockProvider(UploadService, MockUploadService),
      mockProvider(UploadValidationService, MockValidator),
      mockProvider(BsModalService, MockModal)
    ],
    entryComponents: [
      MockComponent(ContextBuilderComponent)
    ]
  });

  beforeEach(() => spectator = createComponent({
    props: {
      property: property
    }
  }));

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });

  it('should display required properties', () => {
    spectator.detectChanges();
    expect(spectator.component.typesData[0].text).toBe('Data Variables Type');
    expect(spectator.query('div.units-container > ng-select')).toBeNull();
    expect(spectator.query('div.units-container > div.no-units')).not.toBeNull();
  });

  it('should open context modal', fakeAsync(() => {
    const modal = spectator.fixture.debugElement.injector.get(BsModalService);
    spectator.detectChanges();
    spyOn(spectator.component.typeReselected, 'emit');
    spyOn(modal.onHidden, 'subscribe').and.callThrough();
    spyOn(spectator.component, 'openContextModal').and.callThrough();
    spyOn(modal, 'show').and.callThrough();
    spectator.click('button.btn.select-custom-button');
    spectator.detectChanges();
    expect(spectator.component.openContextModal).toHaveBeenCalled();
    expect(modal.show).toHaveBeenCalled();
    tick();
    spectator.detectChanges();
    expect(modal.onHidden.subscribe).toHaveBeenCalled();
    spectator.detectChanges();
    expect(spectator.component.typeReselected.emit).toHaveBeenCalled();

    // reset typed property to empty instance
    property = new TypedProperty(1, false)
  }));

  it('should call get units on selection', fakeAsync(() => {
    const uploadService = spectator.fixture.debugElement.injector.get(UploadService);
    spectator.detectChanges();
    spyOn(uploadService, 'searchOntPropertyUnits').and.callThrough();
    spyOn(spectator.component, 'setPropertyType').and.callThrough();
    spyOn(spectator.component, 'getPropertyUnits').and.callThrough();
    spectator.triggerEventHandler('ng-select', 'change', properties[0].typeTerm);
    spectator.detectChanges();
    expect(spectator.component.setPropertyType).toHaveBeenCalled();
    spectator.detectChanges();
    expect(spectator.component.getPropertyUnits).toHaveBeenCalled();
    expect(uploadService.searchOntPropertyUnits).toHaveBeenCalled();
    tick();
    spectator.detectChanges();
    expect(spectator.component.unitsData[0].text).toBe('test unit')
  }));

  it('should trigger scalar validation on value field focus out', async(() => {
    spectator.fixture.whenRenderingDone().then(() => {
      jasmine.getEnv().allowRespy(true);
      const validator = spectator.fixture.debugElement.injector.get(UploadValidationService);
      spyOn(validator, 'validScalarType').and.callThrough();
      spyOn(spectator.component, 'validateScalarType').and.callThrough();
      spyOn(spectator.component.valueError, 'emit');

      spectator.typeInElement('test value', 'input.form-control');
      spectator.detectChanges();
      expect(spectator.component.property.value).toBe('test value');

      spectator.triggerEventHandler('input.form-control', 'focusout', {});
      spectator.detectChanges();
      expect(spectator.component.validateScalarType).toHaveBeenCalled();
      expect(validator.validScalarType).toHaveBeenCalled();
      expect(spectator.component.valueError.emit).toHaveBeenCalledWith('invalid value');
      expect(spectator.query('input.form-control')).toHaveClass('button-error');
    });
  }));

  it('should subscribe to errors', () => {
    errorSub.next(true);
    spectator.detectChanges();
    expect(spectator.component.errors).toBeTruthy();
    expect(spectator.query('input.form-control')).toHaveClass('button-error');
  });
});

