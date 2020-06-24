import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory, mockProvider } from '@ngneat/spectator';
import { MockComponent } from 'ng-mocks';
import { DataValuesComponent } from './data-values.component';
import { DataValueFormComponent } from './data-value-form/data-value-form.component';
import { HttpClientModule } from '@angular/common/http';
import { DataValue, Brick, Term } from 'src/app/shared/models/brick';
import { BrickFactoryService } from 'src/app/shared/services/brick-factory.service';
import { UploadService } from 'src/app/shared/services/upload.service';
const templates = require('src/app/shared/test/brick-type-templates.json');

describe('DataValuesComponent', () => {

  const testBrick = BrickFactoryService.createUploadInstance(templates.results[0].children[1]);

  const MockUploadService = {
    getBrickBuilder: () => testBrick
  };

  let spectator: Spectator<DataValuesComponent>;
  const createComponent = createComponentFactory({
    component: DataValuesComponent,
    entryComponents: [
      MockComponent(DataValueFormComponent)
    ],
    imports: [
      HttpClientModule
    ],
    providers: [
      mockProvider(UploadService, MockUploadService)
    ]
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });

  it('should have instance of brick builder', () => {
    expect(spectator.component.brick).toBeTruthy();
    expect(spectator.component.brick instanceof Brick).toBeTruthy();
    expect(spectator.component.brick.template_type).toBe('Test Chemical Measurement');
    expect(spectator.component.dataValues).toHaveLength(2);
  });

  it('should call addDataValue on button click', () => {
    spyOn(spectator.component, 'addDataValue');
    spectator.click('button.btn.btn-link');
    spectator.detectChanges();
    expect(spectator.component.addDataValue).toHaveBeenCalled();
  });

  it('should render data values', () => {
    expect(spectator.queryAll('app-data-value-form')).toHaveLength(2);
  })

  it('should add new dataVar with addDataValue method', () => {
    spectator.component.addDataValue();
    spectator.detectChanges();
    expect(spectator.component.dataValues).toHaveLength(3);
    expect(spectator.queryAll('app-data-value-form')).toHaveLength(3);
  });

  it('should reset datavars', () => {
    spectator.component.dataValues[2].units = new Term('id', 'text');
    spectator.component.resetDataValue(new DataValue(2, false), 2);
    spectator.detectChanges(); 
    expect(spectator.component.dataValues[2].units).toBeUndefined();
  });

  it('should remove dataVars', () => {
    spectator.component.removeDataValue(2);
    spectator.detectChanges();
    expect(spectator.component.dataValues).toHaveLength(2);
  });
});
