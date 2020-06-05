import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory, mockProvider } from '@ngneat/spectator';
import { HttpClientModule } from '@angular/common/http';
import { LoadSuccessTableComponent } from './load-success-table.component';
import { Brick } from 'src/app/shared/models/brick';
import { UploadService } from 'src/app/shared/services/upload.service';
import { BrickFactoryService } from 'src/app/shared/services/brick-factory.service';
import { By } from '@angular/platform-browser';
const metadata = require('src/app/shared/test/brick-type-templates.json');

describe('LoadSuccessTableComponent', () => {

  const brick: Brick = BrickFactoryService.createUploadInstance(metadata.results[0].children[1]);

  const MockUploadService = {
    getBrickBuilder: () => brick
  };

  let spectator: Spectator<LoadSuccessTableComponent>;
  const createComponent = createComponentFactory({
    component: LoadSuccessTableComponent,
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

  it('should have brick instance', () => {
    spectator.detectChanges();
    expect(spectator.component.brick).toEqual(brick);
  });

  it('should render dim var info', () => {
    expect(spectator.queryAll('table.dim-var-info-table')).toHaveLength(2);
    expect(spectator.queryAll('table.dim-var-info-table > tbody > tr')).toHaveLength(5);
    expect(spectator.query('table.dim-var-info-table > tbody > tr:nth-child(2)'))
      .toHaveDescendantWithText({
        selector: 'td:nth-child(2)',
        text: 'Volume  , State=extracted from sediment'
      });
    expect(spectator.query('table.dim-var-info-table > tbody> tr:nth-child(2)'))
      .toHaveDescendantWithText({
        selector: 'td:nth-child(3)',
        text: 'microliter'
      });
  });

  it('should render data var info', () => {
    expect(spectator.queryAll('table#data-var-info-table > tbody > tr')).toHaveLength(2);
    expect(spectator.query('table#data-var-info-table > tbody > tr:nth-child(2)'))
      .toHaveDescendantWithText({
        selector: 'td:nth-child(2)',
        text: 'Below  , Relative=detection limit'
      });
    expect(spectator.query('table#data-var-info-table > tbody > tr'))
      .toHaveDescendantWithText({
        selector: 'td:nth-child(3)',
        text: 'milligram per liter'
      });
  });
});
